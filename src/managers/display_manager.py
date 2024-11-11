# src/display/display_manager.py
from PIL import Image, ImageDraw, ImageFont
import threading

class DisplayManager:
    def __init__(self, oled, config):
        self.oled = oled
        self.config = config
        self.lock = threading.Lock()

        # Load fonts
        self.fonts = {}
        for key, path in config['fonts'].items():
            try:
                size = 20 if 'large' in key else 12  # Example sizing
                self.fonts[key] = ImageFont.truetype(path, size=size)
            except IOError:
                print(f"Font file not found at {path}. Using default font.")
                self.fonts[key] = ImageFont.load_default()

    def clear_screen(self):
        with self.lock:
            blank_image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
            self.oled.display(blank_image)
            print("DisplayManager: Screen cleared.")

    def display_image(self, image_path, resize=True):
        with self.lock:
            try:
                image = Image.open(image_path).convert(self.oled.mode)
                if resize:
                    image = image.resize((self.oled.width, self.oled.height))
                self.oled.display(image)
                print(f"DisplayManager: Displayed image {image_path}.")
            except IOError:
                print(f"DisplayManager: Failed to load image {image_path}.")

    def display_text(self, text, position, font_key, fill="white"):
        with self.lock:
            image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
            draw = ImageDraw.Draw(image)
            font = self.fonts.get(font_key, ImageFont.load_default())
            draw.text(position, text, font=font, fill=fill)
            self.oled.display(image)
            print(f"DisplayManager: Displayed text '{text}' at {position}.")

    def draw_custom(self, draw_function):
        with self.lock:
            image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
            draw = ImageDraw.Draw(image)
            draw_function(draw)
            self.oled.display(image)
            print("DisplayManager: Executed custom draw function.")
