from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
import threading
import os
import time

class DisplayManager:
    def __init__(self, config):
        # Initialize SPI connection for the SSD1322 OLED display
        self.serial = spi(device=0, port=0)  # Default SPI device
        self.oled = ssd1322(self.serial, width=256, height=64)
        
        self.config = config
        self.lock = threading.Lock()
        
        # Load fonts from configuration
        self.fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        """Load fonts as specified in the configuration with error handling."""
        fonts_config = self.config.get('fonts', {})
        default_font = ImageFont.load_default()

        for key, font_info in fonts_config.items():
            path = font_info.get('path')
            size = font_info.get('size', 12)
            font_path = os.path.join(os.path.dirname(__file__), '../assets/fonts', path) if not os.path.isabs(path) else path
            try:
                self.fonts[key] = ImageFont.truetype(font_path, size=size)
            except IOError:
                print(f"Font file not found at {font_path}. Using default font.")
                self.fonts[key] = default_font

    def clear_screen(self):
        """Clears the OLED screen by displaying a blank image."""
        with self.lock:
            blank_image = Image.new(self.oled.mode, self.oled.size, "black")
            self.oled.display(blank_image)
            print("DisplayManager: Screen cleared.")

    def display_image(self, image_path, resize=True, timeout=None):
        """Displays an image with an optional timeout to clear the screen."""
        with self.lock:
            try:
                image = Image.open(image_path).convert(self.oled.mode)
                if resize:
                    image = image.resize(self.oled.size)
                self.oled.display(image)
                print(f"DisplayManager: Displayed image '{image_path}'.")

                # Start a timeout to clear the screen if specified
                if timeout:
                    timer = threading.Timer(timeout, self.clear_screen)
                    timer.start()

            except IOError:
                print(f"DisplayManager: Failed to load image '{image_path}'.")

    def display_text(self, text, position, font_key='default', fill="white"):
        """Displays text at a specified position using a specified font."""
        with self.lock:
            image = Image.new(self.oled.mode, self.oled.size, "black")
            draw = ImageDraw.Draw(image)
            font = self.fonts.get(font_key, ImageFont.load_default())
            draw.text(position, text, font=font, fill=fill)
            self.oled.display(image)
            print(f"DisplayManager: Displayed text '{text}' at {position} with font '{font_key}'.")

    def draw_custom(self, draw_function):
        """Executes a custom drawing function onto the OLED."""
        with self.lock:
            image = Image.new(self.oled.mode, self.oled.size, "black")
            draw = ImageDraw.Draw(image)
            draw_function(draw)
            self.oled.display(image)
            print("DisplayManager: Executed custom draw function.")
