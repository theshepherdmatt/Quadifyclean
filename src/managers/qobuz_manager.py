# src/managers/qobuz_manager.py
from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw
import threading

class QobuzManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.qobuz_playlists = []
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed
        self.logger.info("QobuzManager initialized.")

        # Connect to VolumioListener signals
        self.volumio_listener.qobuz_playlists_received.connect(self.update_qobuz_playlists)
        self.logger.debug("Connected to VolumioListener's qobuz_playlists_received signal.")

        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        self.logger.debug("Registered mode change callback.")

        self.lock = threading.Lock()

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.logger.info("QobuzManager: Starting Qobuz mode.")
        if not self.qobuz_playlists:
            self.display_loading_screen()
            self.volumio_listener.fetch_qobuz_playlists()
            self.logger.info("QobuzManager: Fetching Qobuz playlists.")
        else:
            self.display_qobuz_playlists()
            self.logger.info("QobuzManager: Displaying existing Qobuz playlists.")

    def stop_mode(self):
        if not self.is_active:
            self.logger.debug("stop_mode called, but mode is already inactive.")  # Corrected to use self.logger
            return
        self.is_active = False
        self.display_manager.clear_screen()
        self.logger.info("QobuzManager: Stopped Qobuz mode and cleared display.")  # Corrected to use self.logger

    def update_qobuz_playlists(self, playlists):
        with self.lock:
            self.qobuz_playlists = playlists or []
            self.logger.debug(f"QobuzManager: Updated Qobuz playlists: {[playlist['title'] for playlist in self.qobuz_playlists]}")
            if self.is_active:
                if self.qobuz_playlists:
                    self.display_qobuz_playlists()
                else:
                    self.display_no_playlists()

    def display_qobuz_playlists(self):
        self.logger.info("QobuzManager: Displaying Qobuz playlists.")
        def draw(draw_obj):
            y_offset = 10
            for i, playlist in enumerate(self.qobuz_playlists):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{playlist['title']}",
                    font=self.display_manager.fonts.get(self.font_key, ImageFont.load_default()),
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)
        self.logger.debug("QobuzManager: draw_custom called to display Qobuz playlists.")

    def scroll_selection(self, direction):
        if not self.is_active:
            self.logger.debug("QobuzManager: Scroll attempted while not active.")
            return
        with self.lock:
            self.current_selection_index = (self.current_selection_index + direction) % len(self.qobuz_playlists)
            self.display_qobuz_playlists()
            self.logger.debug(f"QobuzManager: Scrolled to Qobuz playlist index: {self.current_selection_index}")

    def select_item(self):
        if not self.is_active or not self.qobuz_playlists:
            self.logger.warning("QobuzManager: Select attempted while inactive or no playlists available.")
            return
        selected_playlist = self.qobuz_playlists[self.current_selection_index]
        self.logger.info(f"QobuzManager: Selected Qobuz playlist: {selected_playlist['title']}")
        self.volumio_listener.play_qobuz_playlist(
            title=selected_playlist['title'],
            uri=selected_playlist['uri']
        )

    def display_loading_screen(self):
        self.display_manager.display_text(
            "Loading Qobuz Playlists...",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.debug("QobuzManager: Displayed loading screen for Qobuz playlists.")

    def display_no_playlists(self):
        self.display_manager.display_text(
            "No Qobuz Playlists Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.warning("QobuzManager: No Qobuz playlists available to display.")

    def handle_mode_change(self, current_mode):
        if current_mode == "qobuz":
            self.logger.info("QobuzManager: Entering Qobuz mode.")
            self.start_mode()
        else:
            if self.is_active:
                self.logger.info("QobuzManager: Exiting Qobuz mode.")
                self.stop_mode()
