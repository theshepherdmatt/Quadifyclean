import RPi.GPIO as GPIO
import time
import requests  # Import to make HTTP requests for volume control

class RotaryControl:
    LEFT = 1
    RIGHT = 2

    def __init__(self, clk_pin=13, dt_pin=5, sw_pin=6, debounce_delay=0.01, rotation_callback=None, button_callback=None, mode_manager=None):
        # Initialize GPIO pins
        self.CLK_PIN = clk_pin
        self.DT_PIN = dt_pin
        self.SW_PIN = sw_pin
        self.rotation_callback = rotation_callback  # Callback for rotation events
        self.button_callback = button_callback  # Callback for button press
        self.debounce_delay = debounce_delay
        self.direction = None
        self.last_state = 0b11  # Initial state of (CLK, DT) as binary
        self.last_rotation_time = time.time()
        self.last_button_press_time = 0  # Initialize last button press time for debounce
        self.mode_manager = mode_manager

        self.VOL_API_URL = "http://localhost:3000/api/v1/commands/?cmd=volume&volume="  # URL to control Volumio volume

        self.setup_gpio()

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Remove existing event detection for CLK_PIN, DT_PIN, and SW_PIN if already added
        try:
            GPIO.remove_event_detect(self.CLK_PIN)
        except RuntimeError:
            pass

        try:
            GPIO.remove_event_detect(self.DT_PIN)
        except RuntimeError:
            pass

        try:
            GPIO.remove_event_detect(self.SW_PIN)
        except RuntimeError:
            pass

        # Interrupt-based detection for rotary encoder rotation
        GPIO.add_event_detect(self.CLK_PIN, GPIO.BOTH, callback=self.handle_rotation)
        GPIO.add_event_detect(self.DT_PIN, GPIO.BOTH, callback=self.handle_rotation)

        # Button press detection
        GPIO.add_event_detect(self.SW_PIN, GPIO.FALLING, callback=self._handle_button_press_internal, bouncetime=1000)

    def handle_rotation(self, channel):
        current_time = time.time()
        if current_time - self.last_rotation_time < self.debounce_delay:
            return  # Ignore if this event occurred too soon after the last one

        self.last_rotation_time = current_time

        # Read the current states of CLK and DT
        clk_state = GPIO.input(self.CLK_PIN)
        dt_state = GPIO.input(self.DT_PIN)
        current_state = (clk_state << 1) | dt_state

        # Detect direction based on specific transitions
        direction_value = None
        if self.last_state == 0b11:  # Both CLK and DT are high
            if current_state == 0b01:  # Clockwise
                direction_value = 1
                print("Rotary turned clockwise (down).")
            elif current_state == 0b10:  # Counterclockwise
                direction_value = -1
                print("Rotary turned counterclockwise (up).")

            # If we have a valid direction, handle the rotation based on the current mode
            if direction_value is not None and self.mode_manager:
                current_mode = self.mode_manager.get_mode()
                print(f"Current mode: {current_mode}")

                # Call the rotation callback with the direction value
                if current_mode in ["menu", "webradio", "playlist"] and self.rotation_callback:
                    self.rotation_callback(direction_value)
                elif current_mode == "playback":
                    # Adjust volume in playback mode
                    volume_change = 15 if direction_value == 1 else -15
                    self.adjust_volume(volume_change)
                else:
                    print(f"Unhandled mode '{current_mode}' in handle_rotation")

        self.last_state = current_state


    def adjust_volume(self, volume_change):
        """Adjusts the volume by the specified amount (+/- 15%). Only call this in playback mode."""
        try:
            response = requests.get("http://localhost:3000/api/v1/getState")
            if response.status_code == 200:
                data = response.json()
                current_volume = data.get("volume", 0) or 0  # Set to 0 if unavailable
                new_volume = max(0, min(100, current_volume + volume_change))
                requests.get(f"{self.VOL_API_URL}{new_volume}")
                print(f"Volume adjusted to: {new_volume}%")
            else:
                print(f"Failed to get current volume from Volumio. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error adjusting volume: {e}")

    def _handle_button_press_internal(self, channel):
        current_time = time.time()

        # Check if enough time has passed since the last button press to consider this a valid new press
        debounce_threshold = 0.5  # 500 milliseconds debounce
        if current_time - self.last_button_press_time < debounce_threshold:
            print("Button press ignored due to debounce.")
            return

        # Update the last button press time
        self.last_button_press_time = current_time

        print("Button pressed.")  # Debug print to confirm button press

        # Delegate button press action to the button callback provided by main.py
        if self.button_callback:
            self.button_callback()

    def stop(self):
        GPIO.remove_event_detect(self.CLK_PIN)
        GPIO.remove_event_detect(self.DT_PIN)
        GPIO.remove_event_detect(self.SW_PIN)
        print("Stopped rotary control and cleaned up GPIO.")
