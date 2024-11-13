# src/hardware/buttonsleds.py

import smbus2
import time
import threading
import logging
from enum import IntEnum
import yaml
from pathlib import Path

# MCP23017 Register Definitions
MCP23017_IODIRA = 0x00
MCP23017_IODIRB = 0x01
MCP23017_GPIOA = 0x12
MCP23017_GPIOB = 0x13
MCP23017_GPPUA = 0x0C
MCP23017_GPPUB = 0x0D

# Default MCP23017 address if not provided in config.yaml
DEFAULT_MCP23017_ADDRESS = 0x20

# Define LED Constants using IntEnum for clarity
class LED(IntEnum):
    LED1 = 0b10000000  # GPIOA7 - Play LED
    LED2 = 0b01000000  # GPIOA6 - Pause LED
    LED3 = 0b00100000  # GPIOA5 - Button 1 LED
    LED4 = 0b00010000  # GPIOA4 - Button 2 LED
    LED5 = 0b00001000  # GPIOA3 - Button 3 LED
    LED6 = 0b00000100  # GPIOA2 - Button 4 LED
    LED7 = 0b00000010  # GPIOA1 - Button 5 LED
    LED8 = 0b00000001  # GPIOA0 - Button 6 LED

class ButtonsLEDController:
    def __init__(self, volumio_listener, config_path='config.yaml', debounce_delay=0.1):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bus = smbus2.SMBus(1)  # Instantiate SMBus directly
        self.debounce_delay = debounce_delay
        self.prev_button_state = [[1, 1], [1, 1], [1, 1], [1, 1]]
        self.button_map = [[1, 2], [3, 4], [5, 6], [7, 8]]
        self.volumio_listener = volumio_listener
        self.status_led_state = 0
        self.current_button_led_state = 0
        self.current_led_state = 0

        # Load the MCP23017 address from config file or use the default address
        self.mcp23017_address = self._load_mcp_address(config_path)

        self._initialize_mcp23017()
        self.register_volumio_callbacks()

    def _load_mcp_address(self, config_path):
        config_file = Path(config_path)
        if config_file.is_file():
            with open(config_file, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    return config.get('mcp23017_address', DEFAULT_MCP23017_ADDRESS)
                except yaml.YAMLError as e:
                    self.logger.error(f"Error reading config file: {e}")
        self.logger.warning(f"Configuration file {config_path} not found or invalid. Using default MCP23017 address.")
        return DEFAULT_MCP23017_ADDRESS

    def _initialize_mcp23017(self):
        try:
            # Set direction for GPIOA (all outputs for LEDs)
            self.bus.write_byte_data(self.mcp23017_address, MCP23017_IODIRA, 0x00)
            # Set direction for GPIOB (inputs for buttons)
            self.bus.write_byte_data(self.mcp23017_address, MCP23017_IODIRB, 0xFF)
            # Enable pull-up resistors on GPIOB
            self.bus.write_byte_data(self.mcp23017_address, MCP23017_GPPUB, 0xFF)
            # Initialize GPIOA outputs to 0
            self.bus.write_byte_data(self.mcp23017_address, MCP23017_GPIOA, 0x00)
            self.logger.info("MCP23017 initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing MCP23017: {e}")
            self.bus = None  # Disable bus to prevent further operations

    def register_volumio_callbacks(self):
        self.volumio_listener.state_changed.connect(self.on_state)
        self.volumio_listener.connected.connect(self.on_connect)
        self.volumio_listener.disconnected.connect(self.on_disconnect)

    def on_connect(self):
        self.logger.info("Connected to Volumio via SocketIO.")

    def on_disconnect(self):
        self.logger.warning("Disconnected from Volumio's SocketIO server.")

    def on_state(self, sender, state):
        new_status = state.get("status")
        if new_status:
            self.logger.debug(f"Volumio status: {new_status.upper()}")
        self.update_status_leds(new_status)

    def start(self):
        """Starts the button monitoring loop."""
        self.running = True
        self.thread = threading.Thread(target=self.check_buttons_and_update_leds)
        self.thread.start()
        self.logger.info("ButtonsLEDController started.")

    def stop(self):
        """Stops the button monitoring loop."""
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join()
        self.logger.info("ButtonsLEDController stopped.")

    def read_button_matrix(self):
        button_matrix_state = [[1, 1], [1, 1], [1, 1], [1, 1]]
        
        if not self.bus:
            self.logger.error("I2C bus not initialized, cannot read button matrix.")
            return button_matrix_state

        for col in range(2):
            try:
                # Set one column low at a time
                col_output = ~(1 << col) & 0x03
                self.bus.write_byte_data(self.mcp23017_address, MCP23017_GPIOA, col_output)
                time.sleep(0.005)
                row_input = self.bus.read_byte_data(self.mcp23017_address, MCP23017_GPIOB)
                for row in range(4):
                    button_matrix_state[row][col] = (row_input >> row) & 0x01
            except Exception as e:
                self.logger.error(f"Error reading button matrix: {e}")
                break  # Stop reading on error
        return button_matrix_state
        
    def check_buttons_and_update_leds(self):
        while self.running:
            if not self.bus:
                self.logger.error("I2C bus not initialized, stopping button monitoring.")
                break
            
            try:
                button_matrix = self.read_button_matrix()
                for row in range(4):
                    for col in range(2):
                        button_id = self.button_map[row][col]
                        current_button_state = button_matrix[row][col]
                        if current_button_state == 0 and self.prev_button_state[row][col] != current_button_state:
                            self.logger.info(f"Button {button_id} pressed")
                            self.handle_button_press(button_id)
                        self.prev_button_state[row][col] = current_button_state
                time.sleep(self.debounce_delay)
            except Exception as e:
                self.logger.error(f"Error in button monitoring loop: {e}")

    def handle_button_press(self, button_id):
        led_to_light = None
        # Reset current button LED
        self.current_button_led_state = 0

        if button_id == 1:
            self.volumio_listener.socketIO.emit('pause')
            led_to_light = None  # Play/Pause LEDs are handled via Volumio state
        elif button_id == 2:
            self.volumio_listener.socketIO.emit('play')
            led_to_light = None  # Play/Pause LEDs are handled via Volumio state
        elif button_id == 3:
            self.volumio_listener.socketIO.emit('next')
            led_to_light = LED.LED4
            self.status_led_state = LED.LED1.value  # Ensure Play LED is lit
        elif button_id == 4:
            self.volumio_listener.socketIO.emit('previous')
            led_to_light = LED.LED3
            self.status_led_state = LED.LED1.value  # Ensure Play LED is lit
        elif button_id == 5:
            self.volumio_listener.socketIO.emit('repeat')
            led_to_light = LED.LED5
        elif button_id == 6:
            self.volumio_listener.socketIO.emit('random')
            led_to_light = LED.LED6
        elif button_id == 7:
            self.logger.info("Add to favourites functionality not implemented yet.")
            led_to_light = LED.LED7
        elif button_id == 8:
            self.logger.info("Restart OLED service functionality not implemented yet.")
            led_to_light = LED.LED8

        if led_to_light:
            self.current_button_led_state = led_to_light.value
        else:
            self.current_button_led_state = 0

        self.control_leds()

    def control_leds(self):
        total_state = self.status_led_state | self.current_button_led_state
        if total_state != self.current_led_state:
            try:
                self.bus.write_byte_data(self.mcp23017_address, MCP23017_GPIOA, total_state)
                self.current_led_state = total_state
                self.logger.debug(f"LED state updated: {bin(total_state)}")
            except Exception as e:
                self.logger.error(f"Error setting LED state: {e}")

    def update_status_leds(self, new_status):
        if new_status == "play":
            self.status_led_state = LED.LED1.value  # Play LED on
            self.status_led_state &= ~LED.LED2.value  # Ensure Pause LED is off
        elif new_status in ["pause", "stop"]:
            self.status_led_state = LED.LED2.value  # Pause LED on
            self.status_led_state &= ~LED.LED1.value  # Ensure Play LED is off
        else:
            self.status_led_state = 0  # Clear status LEDs
        self.control_leds()