# src/managers/playback_manager.py

from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import requests
from io import BytesIO
import hashlib
import os
import threading
import time

class WebradioManager:
    def __init__(self, display_manager):
        self.display_manager = display_manager
        self.local_album_art_path = "/home/volumio/Quadifyclean/src/assets/images/webradio.bmp"
        self.cache_dir = "/home/volumio/Quadifyclean/src/cache/album_art"
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load the local BMP fallback album art once during initialization
        try:
            self.default_album_art = Image.open(self.local_album_art_path).resize((60, 60)).convert("RGBA")
            self.display_manager.logger.info("WebradioManager: Loaded default album art.")
        except IOError:
            self.display_manager.logger.warning("WebradioManager: Local BMP album art not found. Please check the path.")
            self.default_album_art = None

    def fetch_album_art(self, url):
        """Fetches album art from URL with caching."""
        hash_url = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{hash_url}.png")

        if os.path.isfile(cache_path):
            self.display_manager.logger.info("WebradioManager: Loaded album art from cache.")
            return Image.open(cache_path).resize((60, 60)).convert("RGBA")

        try:
            response = requests.get(url)
            if response.headers["Content-Type"].startswith("image"):
                album_art = Image.open(BytesIO(response.content)).resize((60, 60)).convert("RGBA")
                album_art.save(cache_path)
                self.display_manager.logger.info("WebradioManager: Fetched and cached album art from URL.")
                return album_art
        except requests.RequestException:
            self.display_manager.logger.warning("WebradioManager: Failed to fetch album art.")
        except UnidentifiedImageError:
            self.display_manager.logger.warning("WebradioManager: Unsupported image format for album art.")

        return self.default_album_art

    def draw_webradio(self, base_image, data):
        """
        Draws the WebRadio-specific display elements.
        """
        draw = ImageDraw.Draw(base_image)

        # Draw the "WebRadio" station name centered
        station_name = data.get("title", "WebRadio")
        font = self.display_manager.fonts.get('playback_medium', ImageFont.load_default())
        draw.text(
            (self.display_manager.oled.width // 2, 10),
            station_name,
            font=font,
            fill="white",
            anchor="mm"
        )
        self.display_manager.logger.info("WebradioManager: Drew station name.")

        # Attempt to load album art from URL
        album_art_url = data.get("albumart")
        album_art = None

        if album_art_url:
            album_art = self.fetch_album_art(album_art_url)

        # Fallback to default album art if URL fetching fails
        if album_art is None and self.default_album_art:
            album_art = self.default_album_art
            self.display_manager.logger.info("WebradioManager: Using default album art.")

        # Paste album art on display if available
        if album_art:
            # Position album art at the top-right corner with some padding
            album_art_x = self.display_manager.oled.width - album_art.width - 5
            album_art_y = 0
            base_image.paste(album_art, (album_art_x, album_art_y), album_art)
            self.display_manager.logger.info("WebradioManager: Pasted album art onto display.")

class PlaybackManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager=None):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed

        self.webradio = WebradioManager(display_manager)
        self.previous_service = None

        # State management attributes
        self.latest_state = None
        self.state_lock = threading.Lock()
        self.update_event = threading.Event()
        self.stop_event = threading.Event()

        # Start the background update thread
        self.update_thread = threading.Thread(target=self.update_display_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("PlaybackManager: Started background update thread.")

        # Register a callback for Volumio state changes
        self.volumio_listener.state_changed.connect(self.on_volumio_state_change)
        self.logger.info("PlaybackManager initialized.")

    def on_volumio_state_change(self, state):
        """
        Callback to handle state changes from VolumioListener.
        Instead of immediately updating the display, store the state and signal the update thread.
        """
        with self.state_lock:
            self.latest_state = state
        self.update_event.set()
        self.logger.debug("PlaybackManager: Received new state and signaled update thread.")

    def update_display_loop(self):
        """
        Background thread loop that waits for state changes and updates the display at a controlled rate.
        """
        while not self.stop_event.is_set():
            # Wait for an update signal or timeout after 0.1 seconds
            triggered = self.update_event.wait(timeout=0.1)

            if triggered:
                with self.state_lock:
                    state_to_process = self.latest_state
                    self.latest_state = None  # Reset the latest_state

                self.update_event.clear()

                if state_to_process:
                    self.draw_display(state_to_process)

    def draw_display(self, data):
        """Draw the display based on the Volumio state."""
        current_service = data.get("service", "default").lower()

        # Check if the service has changed
        if current_service != self.previous_service:
            self.display_manager.clear_screen()
            self.logger.info(f"PlaybackManager: Service changed to '{current_service}'. Screen cleared.")
            self.previous_service = current_service

        # Create an image to draw on
        base_image = Image.new("RGB", self.display_manager.oled.size, "black")
        draw = ImageDraw.Draw(base_image)

        # Draw volume indicator
        volume = max(0, min(int(data.get("volume", 0)), 100))
        filled_squares = round((volume / 100) * 6)
        square_size = 4
        row_spacing = 4
        padding_bottom = 12
        columns = [8, 28]  # X positions for two columns

        for x in columns:
            for row in range(filled_squares):
                y = self.display_manager.oled.height - padding_bottom - ((row + 1) * (square_size + row_spacing))
                draw.rectangle([x, y, x + square_size, y + square_size], fill="white")
        self.logger.info(f"PlaybackManager: Drew volume bars with {filled_squares} filled squares.")

        if current_service == "webradio":
            # Use WebradioManager to handle WebRadio-specific drawing
            self.webradio.draw_webradio(base_image, data)
        else:
            # Handle general playback drawing
            self.draw_general_playback(draw, base_image, data, current_service)

        # Display the final composed image
        self.display_manager.oled.display(base_image)
        self.logger.info("PlaybackManager: Display updated.")

    def draw_general_playback(self, draw, base_image, data, current_service):
        """
        Draws the general playback information (sample rate, service icon, audio type, bitdepth).
        """
        # Draw Sample Rate with 'kHz'
        sample_rate = data.get("samplerate", "0")
        try:
            sample_rate_num = int(float(sample_rate))
        except ValueError:
            sample_rate_num = 0
        sample_rate_text = f"{sample_rate_num} kHz"
        font_sample = self.display_manager.fonts.get('playback_medium', ImageFont.load_default())
        draw.text(
            (self.display_manager.oled.width // 2, 5),
            sample_rate_text,
            font=font_sample,
            fill="white",
            anchor="mm"
        )
        self.logger.info("PlaybackManager: Drew sample rate.")

        # Draw Service Icon
        icon = self.display_manager.icons.get(current_service, self.display_manager.icons.get("default"))
        if icon:
            icon_x = self.display_manager.oled.width - icon.width - 5  # 5 pixels padding from the right
            icon_y = 5  # 5 pixels padding from the top
            base_image.paste(icon, (icon_x, icon_y), icon)
            self.logger.info(f"PlaybackManager: Pasted icon for '{current_service}'.")

        # Draw Audio Type and Bitdepth
        audio_format = data.get("trackType", "Unknown")
        bitdepth = data.get("bitdepth", "N/A")
        format_bitdepth_text = f"{audio_format}/{bitdepth}"
        font_info = self.display_manager.fonts.get('playback_small', ImageFont.load_default())
        draw.text(
            (self.display_manager.oled.width // -20, 40),
            format_bitdepth_text,
            font=font_info,
            fill="white",
            anchor="mm"
        )
        self.logger.info("PlaybackManager: Drew audio format and bitdepth.")

    def display_playback_info(self):
        """Initialize playback display based on the current state."""
        current_state = self.volumio_listener.get_current_state()
        if current_state:
            self.draw_display(current_state)
        else:
            self.logger.warning("PlaybackManager: No current state available to display.")

    def start_mode(self):
        self.is_active = True
        self.logger.info("PlaybackManager: Starting playback mode.")
        # Initialize playback display
        self.display_playback_info()

    def stop_mode(self):
        """Stop the playback display mode."""
        if self.is_active:
            self.is_active = False
            self.stop_event.set()
            self.update_event.set()  # Unblock the update thread if waiting
            self.update_thread.join()
            self.display_manager.clear_screen()
            self.logger.info("PlaybackManager: Stopped playback mode and terminated update thread.")
        else:
            self.logger.info("PlaybackManager: stop_mode called, but was not active.")

    def toggle_play_pause(self):
        """Emit the play/pause command to Volumio."""
        self.logger.info("PlaybackManager: Toggling play/pause.")
        self.volumio_listener.socketIO.emit("toggle")
