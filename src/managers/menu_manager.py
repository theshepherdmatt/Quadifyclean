import logging
from PIL import Image, ImageDraw, ImageFont

class MenuManager:
    def __init__(self, display_manager, volumio_listener, mode_manager):
        self.display_manager = display_manager
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager

        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set logging level to INFO or DEBUG as needed
        self.logger.info("MenuManager initialized.")

        # Menu initialization
        self.menu_stack = []  # Stack to keep track of menu levels
        self.current_menu_items = ["Webradio", "Playlists", "Favourites", "Tidal", "Qobuz"]
        self.current_selection_index = 0
        self.is_active = False  # Indicates if menu mode is currently active

        # Font settings
        self.font_key = 'menu_font'  # Define in config.yaml under fonts

        # Register mode change callback
        if hasattr(self.mode_manager, "add_on_mode_change_callback"):
            self.mode_manager.add_on_mode_change_callback(self.handle_mode_change)

    def handle_mode_change(self, current_mode):
        self.logger.info(f"MenuManager handling mode change to: {current_mode}")
        if current_mode == "menu":
            self.logger.info("Entering menu mode...")
            self.start_mode()
        elif self.is_active:
            self.logger.info("Exiting menu mode...")
            self.stop_mode()

    def start_mode(self):
        self.logger.info("MenuManager: Starting menu mode.")
        self.is_active = True
        self.current_selection_index = 0
        self.display_menu()

    def stop_mode(self):
        if not self.is_active:
            self.logger.debug("stop_mode called, but mode is already inactive.")
            return
        self.is_active = False
        self.display_manager.clear_screen()
        self.logger.info("MenuManager: Stopped menu mode and cleared display.")

    def display_menu(self):
        self.logger.info("MenuManager: Displaying menu.")
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
        self.logger.debug("MenuManager: Menu displayed.")

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
        elif self.is_active:
            self.logger.info("MenuManager: Exiting menu mode.")
            self.stop_mode()
