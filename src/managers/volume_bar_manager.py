# src/managers/volume_bar_manager.py

from PIL import Image, ImageDraw
import logging

class VolumeBarManager:
    def __init__(self, display_manager):
        self.display_manager = display_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Volume bar configuration
        self.max_volume = 100
        self.num_squares = 6
        self.square_size = 4
        self.row_spacing = 4
        self.column_x_positions = [8, 28]  # X positions for two columns
        self.padding_bottom = 12

        # Initialize previous volume to handle updates
        self.previous_volume = -1

    def draw_volume_bars(self, volume):
        """Draws the volume bars based on the current volume level."""
        # Clamp volume between 0 and max_volume
        volume = max(0, min(int(volume), self.max_volume))

        if volume == self.previous_volume:
            # No change in volume; no need to redraw
            return

        self.previous_volume = volume

        # Calculate the number of filled squares
        filled_squares = round((volume / self.max_volume) * self.num_squares)

        # Create an image for volume bars
        volume_image = Image.new("RGBA", self.display_manager.oled.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(volume_image)

        # Draw filled squares
        for x in self.column_x_positions:
            for row in range(filled_squares):
                y = self.display_manager.oled.height - self.padding_bottom - ((row + 1) * (self.square_size + self.row_spacing))
                draw.rectangle([x, y, x + self.square_size, y + self.square_size], fill="white")

        # Clear the previous volume bar area
        with self.display_manager.lock:
            base_image = self.display_manager.current_image.copy()
            # Define the volume bar area (assuming it's on the bottom-left)
            volume_bar_area = (
                self.column_x_positions[0] - 2,  # Slight padding
                self.display_manager.oled.height - self.padding_bottom - (self.num_squares * (self.square_size + self.row_spacing)),
                self.column_x_positions[-1] + self.square_size + 2,
                self.display_manager.oled.height
            )
            # Clear the volume bar area
            draw_clear = ImageDraw.Draw(base_image)
            draw_clear.rectangle(volume_bar_area, fill="black")
            # Paste the new volume bars
            base_image.paste(volume_image, (0, 0), volume_image)
            # Update the display
            self.display_manager.oled.display(base_image)
            self.display_manager.current_image = base_image
            self.logger.info(f"VolumeBarManager: Updated volume bars to {filled_squares} filled squares.")

