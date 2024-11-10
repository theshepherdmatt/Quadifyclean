import time
import threading
from PIL import Image, ImageDraw, ImageFont

class Clock:
    def __init__(self, device):
        # Load fonts for the clock display
        font_path = "/home/volumio/Quadifyclean/src/assets/fonts/DSEG7Classic-Light.ttf"
        alt_font_path = "/home/volumio/Quadifyclean/src/assets/fonts/OpenSans-Regular.ttf"
        try:
            self.clock_large_font = ImageFont.truetype(font_path, 35)
            self.clock_small_font = ImageFont.truetype(alt_font_path, 12)
        except IOError:
            print("Font file not found. Please check the font paths.")
            exit()

        # Use the passed device instead of initializing a new one
        self.device = device
        print("OLED display initialized successfully for Clock.")

        self.running = False
        self.update_thread = None

    def draw_clock(self):
        """Draw the current time on the OLED screen."""
        # Create a blank image to draw on
        image = Image.new(self.device.mode, (self.device.width, self.device.height), "black")
        draw = ImageDraw.Draw(image)

        # Get the current time in HH:MM format
        current_time = time.strftime("%H:%M")
        
        # Draw the time in the center of the screen
        draw.text((self.device.width / 2, self.device.height / 2.5), current_time, font=self.clock_large_font, fill="white", anchor="mm")

        # Display the image on the device
        self.device.display(image)

    def start(self):
        """Start the clock display."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self.update_clock)
            self.update_thread.start()
            print("Clock mode started.")

    def stop(self):
        """Stop the clock display cleanly."""
        if self.running:
            self.running = False
            if self.update_thread:
                self.update_thread.join()
            self.draw_black_screen()  # Clear the screen before stopping
            print("Clock mode stopped and screen cleared.")

    def update_clock(self):
        """Update the clock continuously while running."""
        while self.running:
            self.draw_clock()
            time.sleep(1)  # Update every 1 second to keep the time accurate

    def draw_black_screen(self):
        """Clear the screen by drawing a black image."""
        image = Image.new(self.device.mode, (self.device.width, self.device.height), "black")
        self.device.display(image)

# Example usage
if __name__ == "__main__":
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322

    # Initialize the OLED display for standalone usage
    serial = spi(device=0, port=0)
    device = ssd1322(serial, rotate=2)

    clock = Clock(device)
    try:
        clock.start()
        # Keep it running for 10 seconds for demonstration purposes
        time.sleep(10)
    finally:
        clock.stop()
