# src/containers.py
from utils.config_loader import load_config
from dependency_injector import containers, providers
from src.network.volumio_listener import VolumioListener
from src.display.display_manager import DisplayManager
from src.display.clock import Clock
from src.managers.mode_manager import ModeManager
from src.managers.menu_manager import MenuManager
from src.managers.playlist_manager import PlaylistManager
from src.managers.radio_manager import RadioManager
from src.managers.tidal_manager import TidalManager
from src.managers.qobuz_manager import QobuzManager
from src.managers.playback_manager import PlaybackManager
from src.controls.rotary_control import RotaryControl
from src.hardware.buttonsleds import ButtonsLEDController
from src.commands.command_invoker import CommandInvoker
from src.handlers.state_handler import StateHandler
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322

class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for Quadifyclean Project."""
    
    config = providers.Configuration()

    # Display Components
    oled_device = providers.Singleton(
        ssd1322,
        serial=spi(device=0, port=0),
        rotate=2
    )
    display_manager = providers.Singleton(
        DisplayManager,
        oled=oled_device,
        config=config.display
    )

    # Network Components
    volumio_listener = providers.Singleton(
        VolumioListener,
        host=config.volumio.host,
        port=config.volumio.port
    )

    # Managers
    mode_manager = providers.Singleton(
        ModeManager,
        display_manager=display_manager,
        clock=providers.Factory(
            Clock,
            display_manager=display_manager,
            config=config
        ),
        playback=providers.Factory(
            PlaybackManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager'),
        ),
        menu_manager=providers.Factory(
            MenuManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager')
        ),
        playlist_manager=providers.Factory(
            PlaylistManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager')
        ),
        radio_manager=providers.Factory(
            RadioManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager')
        ),
        tidal_manager=providers.Factory(
            TidalManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager')
        ),
        qobuz_manager=providers.Factory(
            QobuzManager,
            display_manager=display_manager,
            volumio_listener=volumio_listener,
            mode_manager=providers.Reference('mode_manager')
        ),
    )

    # Handlers
    state_handler = providers.Factory(
        StateHandler,
        volumio_listener=volumio_listener,
        mode_manager=mode_manager
    )

    # Controls
    rotary_control = providers.Singleton(
        RotaryControl,
        clk_pin=config.pins.clk_pin,
        dt_pin=config.pins.dt_pin,
        sw_pin=config.pins.sw_pin,
        rotation_callback=providers.Callable('on_rotation', lambda direction: None),
        button_callback=providers.Callable('on_button_press', lambda: None)
    )

    button_led_controller = providers.Singleton(
        ButtonsLEDController,
        volumioIO=volumio_listener
    )

    # Command Invoker
    command_invoker = providers.Singleton(
        CommandInvoker
    )
