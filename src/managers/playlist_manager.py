# src/managers/playlist_manager.py
from src.managers.base_manager import BaseManager

class PlaylistManager(BaseManager):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        super().__init__(display_manager, volumio_listener, mode_manager)
        self.playlists = []
        self.current_selection_index = 0
        self.font_key = 'menu_font'  # Define in config.yaml under fonts
        self.display_manager.add_on_mode_change_callback(self.handle_mode_change)

    def start_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        if not self.playlists:
            self.display_loading_screen()
            self.volumio_listener.fetch_playlists()
        else:
            self.display_playlists()

    def stop_mode(self):
        self.is_active = False
        self.clear_display()

    def update_playlists(self, playlists):
        self.playlists = playlists or []
        if self.is_active:
            if self.playlists:
                self.display_playlists()
            else:
                self.display_no_playlists()

    def display_playlists(self):
        def draw(draw_obj):
            y_offset = 10
            for i, playlist in enumerate(self.playlists):
                arrow = "-> " if i == self.current_selection_index else "   "
                draw_obj.text(
                    (10, y_offset + i * 15),
                    f"{arrow}{playlist['title']}",
                    font=self.display_manager.fonts[self.font_key],
                    fill="white" if i == self.current_selection_index else "gray"
                )
        self.display_manager.draw_custom(draw)

    def scroll_selection(self, direction):
        if not self.is_active:
            return
        self.current_selection_index = (self.current_selection_index + direction) % len(self.playlists)
        self.display_playlists()

    def select_item(self):
        if not self.is_active or not self.playlists:
            return
        selected_playlist = self.playlists[self.current_selection_index]
        self.volumio_listener.play_playlist(selected_playlist['title'])

    def display_loading_screen(self):
        self.display_manager.display_text(
            "Loading Playlists...",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )

    def display_no_playlists(self):
        self.display_manager.display_text(
            "No Playlists Found",
            position=(self.display_manager.oled.width // 2, self.display_manager.oled.height // 2),
            font_key='menu_font'
        )

    def handle_mode_change(self, current_mode):
        if current_mode == "playlist":
            self.start_mode()
        else:
            if self.is_active:
                self.stop_mode()
