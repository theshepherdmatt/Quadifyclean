# tests/test_containers.py

import pytest
from src.containers import Container
from dependency_injector.providers import Configuration, Singleton, Factory
from dependency_injector.errors import Error

@pytest.fixture(scope="module")
def container():
    container = Container()
    container.config.from_yaml("config.yaml")  # Ensure config.yaml path is correct or use a test-specific config
    container.wire(modules=[__name__])
    yield container
    container.unwire()

def test_container_initialization(container):
    """Test that the container initializes without errors."""
    assert isinstance(container.config, Configuration), "Config should be loaded as a Configuration instance."
    assert isinstance(container.volumio_listener, Singleton), "VolumioListener should be a Singleton provider."
    assert isinstance(container.playback_manager, Singleton), "PlaybackManager should be a Singleton provider."
    assert isinstance(container.menu_manager, Singleton), "MenuManager should be a Singleton provider."

def test_volumio_listener_initialization(container):
    """Test that VolumioListener initializes correctly."""
    volumio_listener = container.volumio_listener()
    assert volumio_listener is not None, "VolumioListener should not be None"
    assert hasattr(volumio_listener, 'connect'), "VolumioListener should have a connect method"
    assert volumio_listener.is_connected == False, "VolumioListener should start disconnected"

def test_mode_manager_initialization(container):
    """Test that ModeManager initializes and has the correct states."""
    mode_manager = container.mode_manager()
    assert mode_manager is not None, "ModeManager should not be None"
    assert mode_manager.state == 'clock', "ModeManager should initialize with 'clock' state"

def test_display_manager_initialization(container):
    """Test that DisplayManager initializes and is configured correctly."""
    display_manager = container.display_manager()
    assert display_manager is not None, "DisplayManager should not be None"
    assert hasattr(display_manager, 'show_logo'), "DisplayManager should have a show_logo method"

def test_playback_manager_initialization(container):
    """Test that PlaybackManager initializes and depends on VolumioListener."""
    playback_manager = container.playback_manager()
    assert playback_manager is not None, "PlaybackManager should not be None"
    assert playback_manager.volumio_listener is not None, "PlaybackManager should have access to VolumioListener"

def test_menu_manager_initialization(container):
    """Test that MenuManager initializes and uses DisplayManager."""
    menu_manager = container.menu_manager()
    assert menu_manager is not None, "MenuManager should not be None"
    assert menu_manager.display_manager is not None, "MenuManager should use DisplayManager"

def test_rotary_control_initialization(container):
    """Test that RotaryControl initializes and has callback functions."""
    rotary_control = container.rotary_control()
    assert rotary_control is not None, "RotaryControl should not be None"
    assert callable(rotary_control.rotation_callback), "RotaryControl should have a rotation callback"
    assert callable(rotary_control.button_callback), "RotaryControl should have a button callback"

def test_buttons_led_controller_initialization(container):
    """Test that ButtonsLEDController initializes correctly with required dependencies."""
    button_led_controller = container.buttons_led_controller()
    assert button_led_controller is not None, "ButtonsLEDController should not be None"
    assert hasattr(button_led_controller, 'start'), "ButtonsLEDController should have a start method"

def test_mode_transitions(container):
    """Test that ModeManager can transition between states as expected."""
    mode_manager = container.mode_manager()

    # Transition to 'playback' mode
    mode_manager.to_playback()
    assert mode_manager.state == 'playback', "ModeManager should transition to 'playback' mode"

    # Transition back to 'clock' mode
    mode_manager.to_clock()
    assert mode_manager.state == 'clock', "ModeManager should transition back to 'clock' mode"

def test_configuration_loaded(container):
    """Verify that configuration values are loaded into components."""
    config = container.config
    assert config.volumio.host() == "localhost", "Expected host to be 'localhost'"
    assert config.volumio.port() == 3000, "Expected port to be 3000"
    assert config.buttons.debounce_delay() == 0.1, "Expected debounce_delay to be 0.1 seconds"

def test_cleanup(container):
    """Ensure cleanup operations are properly set."""
    rotary_control = container.rotary_control()
    button_led_controller = container.buttons_led_controller()
    
    # Call cleanup methods
    rotary_control.stop()
    button_led_controller.stop()
    
    # Verify cleanup actions if applicable (or use mocks if necessary)
    assert not rotary_control.rotation_callback, "RotaryControl's rotation_callback should be unset after stop"
    assert not button_led_controller, "ButtonLEDController should clean up properly"
