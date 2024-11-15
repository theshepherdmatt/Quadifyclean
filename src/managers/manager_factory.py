# src/managers/manager_factory.py
import logging

class ManagerFactory:
    def __init__(self, display_manager, volumio_listener, mode_manager):
        self.display_manager = display_manager
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager

        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed
        self.logger.info("ManagerFactory initialized.")

    def create_menu_manager(self):
        from src.managers.menu_manager import MenuManager
        self.logger.debug("Creating MenuManager.")
        return MenuManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_playlist_manager(self):
        from src.managers.playlist_manager import PlaylistManager
        self.logger.debug("Creating PlaylistManager.")
        return PlaylistManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_radio_manager(self):
        from src.managers.radio_manager import RadioManager
        self.logger.debug("Creating RadioManager.")
        return RadioManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_tidal_manager(self):
        from src.managers.tidal_manager import TidalManager
        self.logger.debug("Creating TidalManager.")
        return TidalManager(self.display_manager, self.volumio_listener, self.mode_manager)

    def create_qobuz_manager(self):
        from src.managers.qobuz_manager import QobuzManager
        self.logger.debug("Creating QobuzManager.")
        return QobuzManager(self.display_manager, self.volumio_listener, self.mode_manager)
    
    # Add methods for other managers as needed with consistent logging
