# src/display/display_manager.py

import logging
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
import threading
import os
import time


class DisplayManager:
    def __init__(self, config):
        # Initialize SPI connection for the SSD1322 OLED display
        self.serial = spi(device=0, port=0)  # Default SPI device
        self.oled = ssd1322(self.serial, width=256, height=64, rotate=2)

        self.config = config
        self.lock = threading.Lock()

        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.CRITICAL)  # Set to INFO or adjust as needed

        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)  # Adjust as needed

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        if not self.logger.handlers:
            self.logger.addHandler(ch)

        self.logger.info("DisplayManager initialized.")

        # Load fonts and icons
        self.fonts = {}
        self._load_fonts()
        self.icons = {}
        services = ["favourites", "nas", "playlists", "qobuz", "tidal", "webradio", "mpd", "default"]
        icon_dir = "/home/volumio/Quadifyclean/src/assets/images"

        for service in services:
            try:
                icon_path = os.path.join(icon_dir, f"{service}.bmp")
                self.icons[service] = Image.open(icon_path).resize((40, 40)).convert("RGBA")
                self.logger.info(f"Loaded icon for '{service}' from '{icon_path}'.")
            except IOError:
                self.logger.warning(f"Icon for '{service}' not found. Please check the path.")

        # Callback list for mode changes
        self.on_mode_change_callbacks = []
    
    def add_on_mode_change_callback(self, callback):
        """Register a callback to be executed on mode changes."""
        if callable(callback):
            self.on_mode_change_callbacks.append(callback)
            self.logger.debug(f"Added mode change callback: {callback}")
        else:
            self.logger.warning(f"Attempted to add a non-callable callback: {callback}")

    def notify_mode_change(self, current_mode):
        """Invoke all registered callbacks when a mode changes."""
        self.logger.debug(f"Notifying mode change to: {current_mode}")
        for callback in self.on_mode_change_callbacks:
            try:
                callback(current_mode)
                self.logger.debug(f"Successfully executed callback: {callback}")
            except Exception as e:
                self.logger.error(f"Error in callback {callback}: {e}")

    def _load_fonts(self):
        fonts_config = self.config.get('fonts', {})
        default_font = ImageFont.load_default()
        
        for key, font_info in fonts_config.items():
            path = font_info.get('path')
            size = font_info.get('size', 12)
            if path and os.path.isfile(path):
                try:
                    self.fonts[key] = ImageFont.truetype(path, size=size)
                    self.logger.info(f"Loaded font '{key}' from '{path}' with size {size}.")
                except IOError as e:
                    self.logger.error(f"Error loading font '{key}' from '{path}'. Exception: {e}")
                    self.fonts[key] = default_font
            else:
                self.logger.warning(f"Font file not found for '{key}' at '{path}'. Falling back to default font.")
                self.fonts[key] = default_font

        self.logger.info(f"Available fonts after loading: {list(self.fonts.keys())}")

    def clear_screen(self):
        """Clears the OLED screen by displaying a blank image."""
        with self.lock:
            blank_image = Image.new(self.oled.mode, self.oled.size, "black")
            self.oled.display(blank_image)
            self.logger.info("Screen cleared.")

    def display_image(self, image_path, resize=True, timeout=None):
        """Displays an image or animates a GIF if it's an animated file."""
        with self.lock:
            try:
                # Load the image
                image = Image.open(image_path)

                # Check if the image is an animated GIF
                if image.format == "GIF" and getattr(image, "is_animated", False):
                    # Calculate display time per frame (split total time by the number of frames)
                    frame_duration = (timeout or 5) / image.n_frames if timeout else 0.1

                    # Loop through each frame
                    for frame in ImageSequence.Iterator(image):
                        if resize:
                            frame = frame.resize(self.oled.size)
                        self.oled.display(frame.convert(self.oled.mode))
                        time.sleep(frame_duration)  # Display each frame for calculated duration
                    self.logger.info(f"Displayed animated image '{image_path}' with timeout {timeout}.")
                else:
                    # Static image handling
                    if resize:
                        image = image.resize(self.oled.size)
                    self.oled.display(image)
                    self.logger.info(f"Displayed static image '{image_path}'.")

                    # Set timeout for non-animated images if provided
                    if timeout:
                        timer = threading.Timer(timeout, self.clear_screen)
                        timer.start()
                        self.logger.info(f"Set timeout to clear screen after {timeout} seconds.")
            except IOError:
                self.logger.error(f"Failed to load image '{image_path}'.")

    def display_text(self, text, position, font_key='default', fill="white"):
        """Displays text at a specified position using a specified font."""
        with self.lock:
            image = Image.new(self.oled.mode, self.oled.size, "black")
            draw = ImageDraw.Draw(image)
            font = self.fonts.get(font_key, ImageFont.load_default())
            draw.text(position, text, font=font, fill=fill)
            self.oled.display(image)
            self.logger.info(f"Displayed text '{text}' at {position} with font '{font_key}'.")

    def draw_custom(self, draw_function):
        """Executes a custom drawing function onto the OLED."""
        with self.lock:
            image = Image.new(self.oled.mode, self.oled.size, "black")
            draw = ImageDraw.Draw(image)
            draw_function(draw)
            self.oled.display(image)
            self.logger.info("Executed custom draw function.")

    def show_logo(self):
        """Displays the startup logo on the OLED screen for a set duration."""
        logo_path = self.config.get('display', {}).get('logo_path')
        if logo_path:
            self.display_image(logo_path, timeout=5)
            self.logger.info("Displaying startup logo for 5 seconds.")
        else:
            self.logger.warning("No logo path configured.")

    def stop_mode(self):
        self.is_active = False
        self.display_manager.clear_display()
        self.logger.info("MenuManager: Stopped menu mode and cleared display.")