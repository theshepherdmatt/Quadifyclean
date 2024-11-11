# src/managers/menu_manager.py
from src.managers.base_manager import BaseManager

class MenuManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.menu_stack = []
        self.current_menu_items = ["Webradio", "Playlists", "Favourites"]
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        self.display_menu()

    def stop_mode(self):
        self.is_active = False
        self.clear_display()

    def display_menu(self):
        def draw(draw_obj):
            y_offset = 10
            for i, item in enumerate(self.current_menu_items):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{item}",
                    font=self.display_manager.fonts[self.font_key],
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)

    def scroll_selection(self, direction):
        if not self.is_active:
            return
        self.current_selection_index = (self.current_selection_index + direction) % len(self.current_menu_items)
        self.display_menu()

    def select_item(self):
        if not self.is_active or not self.current_menu_items:
            return
        selected_item = self.current_menu_items[self.current_selection_index]
        if selected_item == "Webradio":
            self.mode_manager.to_webradio()
        elif selected_item == "Playlists":
            self.mode_manager.to_playlist()
        elif selected_item == "Favourites":
            self.mode_manager.to_favourites()

    def handle_mode_change(self, current_mode):
        if current_mode == "menu":
            self.start_mode()
        else:
            if self.is_active:
                self.stop_mode()
