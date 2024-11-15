# src/managers/tidal_manager.py
from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw
import threading

class TidalManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.tidal_playlists = []
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed

        # Connect to VolumioListener signals
        self.volumio_listener.tidal_playlists_received.connect(self.update_tidal_playlists)  # Ensure correct signal
        self.logger.debug("Connected to VolumioListener's tidal_playlists_received signal.")

        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        self.logger.debug("Registered mode change callback.")

        self.lock = threading.Lock()

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.logger.info("TidalManager: Starting tidal mode.")
        if not self.tidal_playlists:
            self.display_loading_screen()
            self.volumio_listener.fetch_tidal_playlists()
            self.logger.info("TidalManager: Fetching Tidal playlists.")
        else:
            self.display_tidal_playlists()
            self.logger.info("TidalManager: Displaying existing Tidal playlists.")

    def stop_mode(self):
        self.is_active = False
        self.display_manager.clear_screen()
        self.logger.info("TidalManager: Stopped tidal mode and cleared display.")

    def update_tidal_playlists(self, playlists):
        with self.lock:
            self.tidal_playlists = playlists or []
            self.logger.debug(f"TidalManager: Updated Tidal playlists: {[playlist['title'] for playlist in self.tidal_playlists]}")
            if self.is_active:
                if self.tidal_playlists:
                    self.display_tidal_playlists()
                else:
                    self.display_no_playlists()

    def display_tidal_playlists(self):
        self.logger.info("TidalManager: Displaying Tidal playlists.")
        def draw(draw_obj):
            y_offset = 10
            for i, playlist in enumerate(self.tidal_playlists):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{playlist['title']}",
                    font=self.display_manager.fonts[self.font_key],
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)
        self.logger.debug("TidalManager: draw_custom called to display Tidal playlists.")

    def scroll_selection(self, direction):
        if not self.is_active:
            self.logger.debug("TidalManager: Scroll attempted while not active.")
            return
        with self.lock:
            self.current_selection_index = (self.current_selection_index + direction) % len(self.tidal_playlists)
            self.display_tidal_playlists()
            self.logger.debug(f"TidalManager: Scrolled to Tidal playlist index: {self.current_selection_index}")

    def select_item(self):
        if not self.is_active or not self.tidal_playlists:
            self.logger.warning("TidalManager: Select attempted while inactive or no playlists available.")
            return
        selected_playlist = self.tidal_playlists[self.current_selection_index]
        self.logger.info(f"TidalManager: Selected Tidal playlist: {selected_playlist['title']}")
        self.volumio_listener.play_tidal_playlist(
            title=selected_playlist['title'],
            uri=selected_playlist['uri']
        )

    def display_loading_screen(self):
        self.display_manager.display_text(
            "Loading Tidal Playlists...",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.debug("TidalManager: Displayed loading screen for Tidal playlists.")

    def display_no_playlists(self):
        self.display_manager.display_text(
            "No Tidal Playlists Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.warning("TidalManager: No Tidal playlists available to display.")

    def handle_mode_change(self, current_mode):
        if current_mode == "tidal":
            self.logger.info("TidalManager: Switching to tidal mode.")
            self.start_mode()
        else:
            if self.is_active:
                self.logger.info("TidalManager: Exiting tidal mode.")
                self.stop_mode()
