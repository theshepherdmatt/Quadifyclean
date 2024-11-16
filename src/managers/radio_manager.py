# src/managers/radio_manager.py
from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw
import threading

class RadioManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.radio_stations = []
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed

        # Connect to VolumioListener signals
        self.volumio_listener.webradio_received.connect(self.update_radio_stations)
        self.logger.debug("Connected to VolumioListener's webradio_received signal.")

        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        self.logger.debug("Registered mode change callback.")

        self.lock = threading.Lock()

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.logger.info("RadioManager: Starting radio mode.")
        if not self.radio_stations:
            self.display_loading_screen()
            self.volumio_listener.fetch_webradio_stations()
            self.logger.info("RadioManager: Fetching radio stations.")
        else:
            self.display_radio_stations()
            self.logger.info("RadioManager: Displaying existing radio stations.")

    def stop_mode(self):
        if not self.is_active:
            self.logger.debug("stop_mode called, but mode is already inactive.")  # Corrected to use self.logger
            return
        self.is_active = False
        self.display_manager.clear_screen()
        self.logger.info("RadioManager: Stopped Radio mode and cleared display.")  # Corrected to use self.logger

    def update_radio_stations(self, stations):
        with self.lock:
            self.radio_stations = stations or []
            self.logger.debug(f"RadioManager: Updated radio stations: {[station['title'] for station in self.radio_stations]}")
            if self.is_active and self.radio_stations:
                self.display_radio_stations()
            elif self.is_active:
                self.display_no_stations()

    def display_radio_stations(self):
        self.logger.info("RadioManager: Displaying radio stations.")
        def draw(draw_obj):
            y_offset = 10
            for i, station in enumerate(self.radio_stations):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{station['title']}",
                    font=self.display_manager.fonts[self.font_key],
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)
        self.logger.debug("RadioManager: draw_custom called to display radio stations.")

    def scroll_selection(self, direction):
        if not self.is_active:
            self.logger.debug("RadioManager: Scroll attempted while not active.")
            return
        with self.lock:
            self.current_selection_index = (self.current_selection_index + direction) % len(self.radio_stations)
            self.display_radio_stations()
            self.logger.debug(f"RadioManager: Scrolled to radio station index: {self.current_selection_index}")

    def select_item(self):
        if not self.is_active or not self.radio_stations:
            self.logger.warning("RadioManager: Select attempted while inactive or no stations available.")
            return
        selected_station = self.radio_stations[self.current_selection_index]
        self.logger.info(f"RadioManager: Selected radio station: {selected_station['title']}")
        self.volumio_listener.play_webradio_station(
            title=selected_station['title'],
            uri=selected_station['uri']
        )

    def display_loading_screen(self):
        self.display_manager.display_text(
            "Loading Radios...",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.debug("RadioManager: Displayed loading screen for radio stations.")

    def display_no_stations(self):
        self.display_manager.display_text(
            "No Radios Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.warning("RadioManager: No radio stations available to display.")

    def handle_mode_change(self, current_mode):
        if current_mode == "webradio":
            self.logger.info("RadioManager: Switching to webradio mode.")
            self.start_mode()
        elif self.is_active:
            self.logger.info("RadioManager: Exiting webradio mode.")
            self.stop_mode()
