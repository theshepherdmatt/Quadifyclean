# src/managers/manager_factory.py
class ManagerFactory:
    def __init__(self, display_manager, volumio_listener, mode_manager):
        self.display_manager = display_manager
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager

    def create_menu_manager(self):
        from src.managers.menu_manager import MenuManager
        return MenuManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_playlist_manager(self):
        from src.managers.playlist_manager import PlaylistManager
        return PlaylistManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_radio_manager(self):
        from src.managers.radio_manager import RadioManager
        return RadioManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_tidal_manager(self):
        from src.managers.tidal_manager import TidalManager
        return TidalManager(self.display_manager, self.volumio_listener, self.mode_manager)
    
    # Add methods for other managers as needed

