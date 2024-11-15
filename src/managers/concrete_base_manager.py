# src/managers/concrete_base_manager.py

from src.managers.base_manager import BaseManager
from src.display.playback_manager import PlaybackManager
from src.managers.menu_manager import MenuManager
from src.managers.playlist_manager import PlaylistManager
from src.managers.radio_manager import RadioManager
from src.managers.tidal_manager import TidalManager
from src.managers.qobuz_manager import QobuzManager
import logging

class ConcreteBaseManager(BaseManager):
    def __init__(
        self,
        display_manager,
        volumio_listener,
        mode_manager,
        playback_manager: PlaybackManager,
        menu_manager: MenuManager,
        playlist_manager: PlaylistManager,
        radio_manager: RadioManager,
        tidal_manager: TidalManager,
        qobuz_manager: QobuzManager,
    ):
        # Initialize BaseManager with required parameters
        super().__init__(display_manager, volumio_listener, mode_manager)
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed
        self.logger.info("ConcreteBaseManager initialized.")

        # Store individual managers
        self.playback_manager = playback_manager
        self.menu_manager = menu_manager
        self.playlist_manager = playlist_manager
        self.radio_manager = radio_manager
        self.tidal_manager = tidal_manager
        self.qobuz_manager = qobuz_manager

        self.logger.debug("Stored all manager instances.")
