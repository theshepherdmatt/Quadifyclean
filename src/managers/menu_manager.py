# src/managers/menu_manager.py

from src.managers.base_manager import BaseManager
import logging
from PIL import Image, ImageDraw, ImageFont

class MenuManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed

        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)  # Adjust as needed

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        if not self.logger.handlers:
            self.logger.addHandler(ch)

        self.logger.info("MenuManager initialized.")

        # Load or initialize menu items
        self.menu_stack = []
        self.current_menu_items = ["Webradio", "Playlists", "Favourites", "Tidal", "Qobuz"]
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts

        # Register mode change callback
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)
        self.logger.debug("MenuManager: Registered mode change callback.")

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.logger.info("MenuManager: Starting menu mode.")
        self.display_menu()

    def stop_mode(self):
        self.is_active = False
        self.display_manager.clear_screen()  # Updated method name
        self.logger.info("MenuManager: Stopped menu mode and cleared display.")

    def display_menu(self):
        self.logger.debug("MenuManager: Displaying menu.")
        def draw(draw_obj):
            y_offset = 10
            for i, item in enumerate(self.current_menu_items):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{item}",
                    font=self.display_manager.fonts.get(self.font_key, ImageFont.load_default()),
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)
        self.logger.info("MenuManager: Menu displayed.")

    def scroll_selection(self, direction):
        if not self.is_active:
            self.logger.debug("MenuManager: Scroll attempted while not active.")
            return
        previous_index = self.current_selection_index
        self.current_selection_index = (self.current_selection_index + direction) % len(self.current_menu_items)
        self.display_menu()
        self.logger.debug(f"MenuManager: Scrolled selection from {previous_index} to {self.current_selection_index}.")

    def select_item(self):
        if not self.is_active or not self.current_menu_items:
            self.logger.warning("MenuManager: Select attempted while inactive or no menu items available.")
            return
        selected_item = self.current_menu_items[self.current_selection_index]
        self.logger.info(f"MenuManager: Selected menu item: {selected_item}")
        if selected_item == "Webradio":
            self.mode_manager.to_webradio()
        elif selected_item == "Playlists":
            self.mode_manager.to_playlist()
        elif selected_item == "Favourites":
            self.mode_manager.to_favourites()
        elif selected_item == "Tidal":
            self.mode_manager.to_tidal()
        elif selected_item == "Qobuz":
            self.mode_manager.to_qobuz()

    def handle_mode_change(self, current_mode):
        if current_mode == "menu":
            self.logger.info("MenuManager: Entering menu mode.")
            self.start_mode()
        else:
            if self.is_active:
                self.logger.info("MenuManager: Exiting menu mode.")
                self.stop_mode()
