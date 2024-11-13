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
        
        # Connect to VolumioListener signals
        self.volumio_listener.webradio_received.connect(self.update_radio_stations)
        
        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        
        self.lock = threading.Lock()

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        if not self.radio_stations:
            print("No radio stations available, displaying loading screen...")
            self.display_loading_screen()
            self.volumio_listener.fetch_webradio_stations()
        else:
            print("Calling display_radio_stations in start_mode...")
            self.display_radio_stations()


    def stop_mode(self):
        self.is_active = False
        self.clear_display()
        self.display_manager.clear_display()

    def update_radio_stations(self, stations):
        with self.lock:
            self.radio_stations = stations or []
            self.logger.debug(f"Updated radio stations: {[station['title'] for station in self.radio_stations]}")
            if self.is_active and self.radio_stations:
                self.display_radio_stations()
            elif self.is_active:
                self.display_no_stations()

    def display_radio_stations(self):
        print("Displaying radio stations")
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
        print("draw_custom called")

    def scroll_selection(self, direction):
        if not self.is_active:
            return
        with self.lock:
            self.current_selection_index = (self.current_selection_index + direction) % len(self.radio_stations)
            self.display_radio_stations()
            self.logger.debug(f"Scrolled to radio station index: {self.current_selection_index}")

    def select_item(self):
        if not self.is_active or not self.radio_stations:
            return
        selected_station = self.radio_stations[self.current_selection_index]
        self.logger.info(f"Selected radio station: {selected_station['title']}")
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
        self.logger.debug("Displayed loading screen for radio stations.")

    def display_no_stations(self):
        self.display_manager.display_text(
            "No Radios Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )
        self.logger.warning("No radio stations available to display.")

    def handle_mode_change(self, current_mode):
        if current_mode == "webradio":
            print("Starting webradio mode")
            self.start_mode()
        elif self.is_active:
            print("Stopping webradio mode")
            self.stop_mode()
