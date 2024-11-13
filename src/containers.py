# src/containers.py

from dependency_injector import containers, providers
import logging
from smbus2 import SMBus
from src.display.display_manager import DisplayManager
from src.display.clock import Clock
from src.managers.mode_manager import ModeManager
from src.managers.menu_manager import MenuManager  # Corrected import
from src.managers.playlist_manager import PlaylistManager
from src.managers.radio_manager import RadioManager
from src.managers.tidal_manager import TidalManager
from src.managers.qobuz_manager import QobuzManager
from src.display.playback_manager import PlaybackManager  # Ensure correct import
from src.controls.rotary_control import RotaryControl
from src.hardware.buttonsleds import ButtonsLEDController
from src.handlers.state_handler import StateHandler
from src.network.volumio_listener import VolumioListener
from src.commands.command_invoker import CommandInvoker

# Setup logging for debugging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Container(containers.DeclarativeContainer):
    
    config = providers.Configuration()


    # Network Components
    volumio_listener = providers.Singleton(
        VolumioListener,
        host=config.volumio.host,
        port=config.volumio.port
    )
    
    buttons_led_controller = providers.Factory(
        ButtonsLEDController,
        volumio_listener=volumio_listener,
        config=config,
        debounce_delay=config.buttons.debounce_delay() if config.buttons.debounce_delay else 0.1,
    )

    display_manager = providers.Singleton(
        DisplayManager,
        config=config
    )

    # Managers (instantiate without mode_manager first)
    clock = providers.Singleton(
        Clock,
        display_manager=display_manager,
        config=config
    )

    playback_manager = providers.Singleton(
        PlaybackManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener
    )

    menu_manager = providers.Singleton(
        MenuManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=None  # Initially None to prevent circular dependency
    )

    playlist_manager = providers.Singleton(
        PlaylistManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=None  # Initially None to prevent circular dependency
    )

    radio_manager = providers.Singleton(
        RadioManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=None  # Initially None to prevent circular dependency
    )

    tidal_manager = providers.Singleton(
        TidalManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=None  # Initially None to prevent circular dependency
    )

    qobuz_manager = providers.Singleton(
        QobuzManager,
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=None  # Initially None to prevent circular dependency
    )

    command_invoker = providers.Singleton(CommandInvoker)

    # Mode Manager
    mode_manager = providers.Singleton(
        ModeManager,
        display_manager=display_manager,
        clock=clock,
        playback_manager=playback_manager,
        menu_manager=menu_manager,
        playlist_manager=playlist_manager,
        radio_manager=radio_manager,
        tidal_manager=tidal_manager,
        qobuz_manager=qobuz_manager
    )

    rotary_control = providers.Factory(
        RotaryControl,
        clk_pin=config.pins.clk_pin(),
        dt_pin=config.pins.dt_pin(),
        sw_pin=config.pins.sw_pin()
    )

    # Handlers
    state_handler = providers.Singleton(
        StateHandler,
        volumio_listener=volumio_listener,
        mode_manager=mode_manager
    )

    # Initialize resources after defining all providers
    def init_resources(self):
        # Any additional initialization can be done here
        logger.debug("Container initialized with all components")
