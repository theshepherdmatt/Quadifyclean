# src/controls/rotary_control.py

import RPi.GPIO as GPIO
import time
import logging
import yaml
from pathlib import Path

class RotaryControl:
    LEFT = -1
    RIGHT = 1

    def __init__(
        self,
        config_path='config.yaml',
        debounce_delay=0.01,
        rotation_callback=None,
        button_callback=None
    ):
        """
        Initializes the RotaryControl, reading pin configuration from config.yaml.
        """
        # Set up logger first to ensure it's available in all methods
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.debounce_delay = debounce_delay
        self.rotation_callback = rotation_callback
        self.button_callback = button_callback

        # Load pins from config
        self.CLK_PIN, self.DT_PIN, self.SW_PIN = self._load_pins(config_path)

        self.last_state = 0b11  # Initial state of (CLK, DT) as binary
        self.last_rotation_time = time.time()
        self.last_button_press_time = 0  # Initialize last button press time for debounce

        self.logger.debug("Initializing RotaryControl.")

        # Set up GPIO after loading pin configurations
        self.setup_gpio()

    def _load_pins(self, config_path):
        """Load CLK, DT, and SW pins from a YAML configuration file."""
        config_file = Path(config_path)
        if config_file.is_file():
            with open(config_file, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    pins = config.get('pins', {})
                    return (
                        pins.get('clk_pin', 13),
                        pins.get('dt_pin', 5),
                        pins.get('sw_pin', 6)
                    )
                except yaml.YAMLError as e:
                    self.logger.error(f"Error reading config file: {e}")
        self.logger.warning(f"Configuration file {config_path} not found or invalid. Using default pins.")
        return 13, 5, 6

    def setup_gpio(self):
        """Sets up GPIO pins and event detection."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Remove existing event detection to prevent duplication
        for pin in [self.CLK_PIN, self.DT_PIN, self.SW_PIN]:
            try:
                GPIO.remove_event_detect(pin)
            except RuntimeError:
                pass  # Event was not set

        # Interrupt-based detection for rotary encoder rotation
        GPIO.add_event_detect(self.CLK_PIN, GPIO.BOTH, callback=self.handle_rotation)
        GPIO.add_event_detect(self.DT_PIN, GPIO.BOTH, callback=self.handle_rotation)

        # Button press detection
        GPIO.add_event_detect(
            self.SW_PIN,
            GPIO.FALLING,
            callback=self._handle_button_press_internal,
            bouncetime=300
        )

        self.logger.debug("GPIO setup complete.")

    def handle_rotation(self, channel):
        """Handles rotary encoder rotation events."""
        current_time = time.time()
        if current_time - self.last_rotation_time < self.debounce_delay:
            return  # Debounce rotation events

        self.last_rotation_time = current_time

        # Read the current states of CLK and DT
        clk_state = GPIO.input(self.CLK_PIN)
        dt_state = GPIO.input(self.DT_PIN)
        current_state = (clk_state << 1) | dt_state

        # Detect direction based on specific transitions
        direction = None
        if self.last_state == 0b11:  # Both CLK and DT are high
            if current_state == 0b01:  # Clockwise
                direction = self.RIGHT
                self.logger.debug("Rotary turned clockwise.")
            elif current_state == 0b10:  # Counterclockwise
                direction = self.LEFT
                self.logger.debug("Rotary turned counterclockwise.")

        if direction and self.rotation_callback:
            self.rotation_callback(direction)

        self.last_state = current_state

    def _handle_button_press_internal(self, channel):
        """Handles internal button press events with debounce."""
        current_time = time.time()
        debounce_threshold = 0.5  # 500 milliseconds debounce
        if current_time - self.last_button_press_time < debounce_threshold:
            self.logger.debug("Button press ignored due to debounce.")
            return

        self.last_button_press_time = current_time
        self.logger.debug("Button pressed.")
        if self.button_callback:
            self.button_callback()

    def stop(self):
        """Cleans up GPIO settings."""
        for pin in [self.CLK_PIN, self.DT_PIN, self.SW_PIN]:
            GPIO.remove_event_detect(pin)
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.cleanup()
        self.logger.info("Stopped RotaryControl and cleaned up GPIO.")
