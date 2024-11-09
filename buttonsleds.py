import smbus
import time
import json
import requests
import subprocess
import socketio
from enum import Enum
import threading

# MCP23017 Register Definitions
MCP23017_ADDRESS = 0x20
MCP23017_IODIRA = 0x00
MCP23017_IODIRB = 0x01
MCP23017_GPIOA = 0x12
MCP23017_GPIOB = 0x13
MCP23017_GPPUA = 0x0C
MCP23017_GPPUB = 0x0D

# Define LED Constants using Enum for clarity
class LED(Enum):
    LED1 = 0b10000000  # GPIOA7 - Play Status
    LED2 = 0b01000000  # GPIOA6 - Pause Status
    LED3 = 0b00100000  # GPIOA5 - Button 1
    LED4 = 0b00010000  # GPIOA4 - Button 2
    LED5 = 0b00001000  # GPIOA3 - Button 3
    LED6 = 0b00000100  # GPIOA2 - Button 4
    LED7 = 0b00000010  # GPIOA1 - Button 5
    LED8 = 0b00000001  # GPIOA0 - Button 6

class ButtonsLEDController:
    def __init__(self, volumioIO, debounce_delay=0.1):
        self.bus = smbus.SMBus(1)
        self.debounce_delay = debounce_delay
        self.prev_button_state = [[1, 1], [1, 1], [1, 1], [1, 1]]
        self.button_map = [[1, 2], [3, 4], [5, 6], [7, 8]]
        self.volumioIO = volumioIO
        self.status_led_state = 0
        self.other_button_led_state = 0
        self.current_led_state = 0
        self._initialize_mcp23017()
        self.register_volumio_callbacks()

    def _initialize_mcp23017(self):
        self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRB, 0x3C)
        self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPPUB, 0x3C)
        self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRA, 0x00)
        self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOA, 0x00)

    def register_volumio_callbacks(self):
        self.volumioIO.on('pushState', self.on_state)
        self.volumioIO.on('connect', self.on_connect)
        self.volumioIO.on('disconnect', self.on_disconnect)

    def on_connect(self):
        print("Connected to Volumio via SocketIO.")

    def on_disconnect(self):
        print("Disconnected from Volumio's SocketIO server.")

    def on_state(self, state):
        new_status = state.get("status")
        if new_status:
            print(f"Volumio status: {new_status.upper()}")
        self.update_status_leds(new_status)

    def start_status_update_loop(self):
        """Periodically fetch and update Volumio's status in a loop."""
        while True:
            try:
                response = requests.get("http://localhost:3000/api/v1/getState")
                if response.status_code == 200:
                    state = response.json().get("status")
                    self.update_status_leds(state)
                else:
                    print(f"Failed to fetch Volumio state. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error fetching Volumio state: {e}")
            time.sleep(5)  # Update interval

    def read_button_matrix(self):
        button_matrix_state = [[1, 1], [1, 1], [1, 1], [1, 1]]
        for column in range(2):
            column_mask = ~(1 << column) & 0x03
            self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB, column_mask)
            time.sleep(0.005)
            row_state = self.bus.read_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB) & 0x3C
            for row in range(4):
                button_matrix_state[row][column] = (row_state >> (row + 2)) & 1
        return button_matrix_state

    def check_buttons_and_update_leds(self):
        while True:
            button_matrix = self.read_button_matrix()
            for row in range(4):
                for col in range(2):
                    button_id = self.button_map[row][col]
                    current_button_state = button_matrix[row][col]
                    if current_button_state == 0 and self.prev_button_state[row][col] != current_button_state:
                        print(f"Button {button_id} pressed")
                        self.handle_button_press(button_id)
                    self.prev_button_state[row][col] = current_button_state
            time.sleep(self.debounce_delay)

    def handle_button_press(self, button_id):
        led_to_flash = None
        if button_id == 1:
            self.execute_volumio_command("pause")
            led_to_flash = LED.LED1
        elif button_id == 2:
            self.execute_volumio_command("play")
            led_to_flash = LED.LED2
        elif button_id == 3:
            self.execute_volumio_command("next")
            led_to_flash = LED.LED4
        elif button_id == 4:
            self.execute_volumio_command("previous")
            led_to_flash = LED.LED3
        elif button_id == 5:
            self.execute_volumio_command("repeat")
            led_to_flash = LED.LED5
        elif button_id == 6:
            self.execute_volumio_command("random")
            led_to_flash = LED.LED6
        elif button_id == 7:
            self.add_to_favourites()
            led_to_flash = LED.LED7
        elif button_id == 8:
            self.restart_oled_service()
            led_to_flash = LED.LED8
        if led_to_flash:
            print(f"LED lit for button {button_id}: {led_to_flash.name}")
            threading.Thread(target=self.flash_led, args=(led_to_flash.value,)).start()

    def flash_led(self, led_value, duration=0.2):
        try:
            self.other_button_led_state |= led_value
            self.control_leds()
            time.sleep(duration)
            self.other_button_led_state &= ~led_value
            self.control_leds()
        except Exception as e:
            print(f"Error flashing LED: {e}")

    def control_leds(self):
        total_state = self.status_led_state | self.other_button_led_state
        if total_state != self.current_led_state:
            try:
                self.bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOA, total_state)
                self.current_led_state = total_state
            except Exception as e:
                print(f"Error setting LED state: {e}")

    def update_status_leds(self, new_status):
        if new_status == "play":
            self.status_led_state = LED.LED1.value  # Play LED on
            self.status_led_state &= ~LED.LED2.value  # Ensure Pause LED is off
        elif new_status in ["pause", "stop"]:  # Handle both pause and stop the same way
            self.status_led_state = LED.LED2.value  # Pause/Stop LED on
            self.status_led_state &= ~LED.LED1.value  # Ensure Play LED is off
        else:
            self.status_led_state = 0  # Clear all status LEDs for any other state
        self.control_leds()


    def execute_volumio_command(self, command):
        cmd = f"volumio {command}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Command '{cmd}' failed with return code {result.returncode}")
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
