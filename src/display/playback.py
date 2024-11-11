# src/managers/playback_manager.py
from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw
import threading

class PlaybackManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.current_track = {}
        self.font_key = 'playback_medium'  # Define in config.yaml under fonts
        self.large_font_key = 'playback_large'  # For track title
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Connect to VolumioListener signals
        self.volumio_listener.state_changed.connect(self.update_playback_state)
        self.volumio_listener.track_changed.connect(self.update_current_track)
        
        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        
        self.lock = threading.Lock()

    def start_mode(self):
        self.is_active = True
        self.logger.debug("Playback mode started.")
        self.display_current_track()

    def stop_mode(self):
        self.is_active = False
        self.clear_display()
        self.logger.debug("Playback mode stopped.")

    def update_playback_state(self, state):
        with self.lock:
            status = state.get("status", "")
            self.logger.debug(f"Received playback state update: {status}")
            if status == "play":
                if not self.is_active:
                    self.start_mode()
            elif status in ["pause", "stop"]:
                if self.is_active:
                    self.stop_mode()
            # Add more state handling as needed

    def update_current_track(self, track_info):
        with self.lock:
            self.current_track = track_info
            self.logger.debug(f"Updated current track: {track_info}")
            if self.is_active:
                self.display_current_track()

    def display_current_track(self):
        def draw(draw_obj):
            if not self.current_track:
                draw_obj.text(
                    (10, 10),
                    "No Track Playing",
                    font=self.display_manager.fonts[self.font_key],
                    fill="white"
                )
                return
            title = self.current_track.get("title", "Unknown Title")
            artist = self.current_track.get("artist", "Unknown Artist")
            album_art = self.current_track.get("albumart", "")
            
            # Display Track Title
            draw_obj.text(
                (10, 10),
                title,
                font=self.display_manager.fonts[self.large_font_key],
                fill="white"
            )
            
            # Display Artist
            draw_obj.text(
                (10, 30),
                f"Artist: {artist}",
                font=self.display_manager.fonts[self.font_key],
                fill="gray"
            )
            
            # Display Album Art if available
            if album_art:
                try:
                    image = Image.open(album_art).convert("RGB")
                    image = image.resize((50, 50))  # Adjust size as needed
                    draw_obj.bitmap((10, 50), image, fill="white")
                except IOError as e:
                    self.logger.error(f"Failed to load album art: {e}")
        
        self.display_manager.draw_custom(draw)
        self.logger.debug("Displayed current track information.")

    def toggle_play_pause(self):
        """Toggles between play and pause states."""
        with self.lock:
            current_state = self.volumio_listener.get_current_state()
            if current_state.get("status", "") == "play":
                self.volumio_listener.pause()
                self.logger.info("Playback paused.")
            else:
                self.volumio_listener.play()
                self.logger.info("Playback started/resumed.")

    def skip_track(self):
        """Skips to the next track."""
        with self.lock:
            self.volumio_listener.next_track()
            self.logger.info("Skipped to the next track.")

    def previous_track(self):
        """Goes back to the previous track."""
        with self.lock:
            self.volumio_listener.previous_track()
            self.logger.info("Went back to the previous track.")

    def adjust_volume(self, increment=5):
        """Adjusts the volume by the specified increment."""
        with self.lock:
            current_volume = self.volumio_listener.get_volume()
            new_volume = min(max(current_volume + increment, 0), 100)
            self.volumio_listener.set_volume(new_volume)
            self.logger.info(f"Volume adjusted to {new_volume}%.")
            if self.is_active:
                self.display_current_track()

    def handle_mode_change(self, current_mode):
        if current_mode == "playback":
            self.start_mode()
        else:
            if self.is_active:
                self.stop_mode()
