# src/managers/playlist_manager.py
from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw, ImageFont
import threading

class PlaylistManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.playlists = []
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed
        self.logger.info("PlaylistManager initialized.")

        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        self.logger.debug("Registered mode change callback.")

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.logger.info("PlaylistManager: Starting playlist mode.")
        if not self.playlists:
            self.display_loading_screen()
            self.volumio_listener.fetch_playlists()
            self.logger.info("PlaylistManager: Fetching playlists.")
        else:
            self.display_playlists()
            self.logger.info("PlaylistManager: Displaying existing playlists.")

    def stop_mode(self):
        if not self.is_active:
            self.logger.debug("stop_mode called, but mode is already inactive.")  # Corrected to use self.logger
            return
        self.is_active = False
        self.display_manager.clear_screen()
        self.logger.info("PlaylistManager: Stopped playlist mode and cleared display.")  # Corrected to use self.logger

    def update_playlists(self, playlists):
        self.playlists = playlists or []
        self.logger.debug(f"PlaylistManager: Updated playlists: {[playlist['title'] for playlist in self.playlists]}")
        if self.is_active:
            if self.playlists:
                self.display_playlists()
            else:
                self.display_no_playlists()

    def display_playlists(self):
        self.logger.info("PlaylistManager: Displaying playlists.")
        def draw(draw_obj):
            y_offset = 10
            for i, playlist in enumerate(self.playlists):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{playlist['title']}",
                    font=self.display_manager.fonts.get(self.font_key, ImageFont.load_default()),
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)
        self.logger.debug("PlaylistManager: draw_custom called to display playlists.")

    def scroll_selection(self, direction):
        if not self.is_active:
            self.logger.debug("PlaylistManager: Scroll attempted while not active.")
            return
        previous_index = self.current_selection_index
        self.current_selection_index = (self.current_selection_index + direction) % len(self.playlists)
        self.display_playlists()
        self.logger.debug(f"PlaylistManager: Scrolled selection from {previous_index} to {self.current_selection_index}.")

    def select_item(self):
        if not self.is_active or not self.playlists:
            self.logger.warning("PlaylistManager: Select attempted while inactive or no playlists available.")
            return
        selected_playlist = self.playlists[self.current_selection_index]
        self.logger.info(f"PlaylistManager: Selected playlist: {selected_playlist['title']}")
        self.volumio_listener.play_playlist(selected_playlist['title'])

    def display_loading_screen(self):
        self.display_manager.display_text(
            "Loading Playlists...",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.debug("PlaylistManager: Displayed loading screen for playlists.")

    def display_no_playlists(self):
        self.display_manager.display_text(
            "No Playlists Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.warning("PlaylistManager: No playlists available to display.")

    def handle_mode_change(self, current_mode):
        if current_mode == "playlist":
            self.logger.info("PlaylistManager: Entering playlist mode.")
            self.start_mode()
        else:
            if self.is_active:
                self.logger.info("PlaylistManager: Exiting playlist mode.")
                self.stop_mode()
