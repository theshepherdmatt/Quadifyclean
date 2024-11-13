# tests/test_containers.py

import pytest
from unittest.mock import MagicMock
from dependency_injector import providers

# Add the project root to sys.path if not already done
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.containers import Container

@pytest.fixture(scope="module")
def container():
    """
    Fixture to set up and return a mocked Container instance.
    """
    container = Container()

    # Configure the container with mock configuration
    container.config.volumio.host.from_value('localhost')
    container.config.volumio.port.from_value(3000)
    container.config.buttons.debounce_delay.from_value(0.2)
    container.config.pins.clk_pin.from_value(17)
    container.config.pins.dt_pin.from_value(18)
    container.config.pins.sw_pin.from_value(27)

    # Mock external dependencies
    volumio_listener_mock = MagicMock()
    display_manager_mock = MagicMock()
    mode_manager_mock = MagicMock()
    buttons_led_controller_mock = MagicMock()
    rotary_control_mock = MagicMock()
    clock_mock = MagicMock()
    playback_manager_mock = MagicMock()
    menu_manager_mock = MagicMock()
    playlist_manager_mock = MagicMock()
    radio_manager_mock = MagicMock()
    tidal_manager_mock = MagicMock()
    qobuz_manager_mock = MagicMock()
    state_handler_mock = MagicMock()

    # Override providers with mocks
    container.volumio_listener.override(providers.Object(volumio_listener_mock))
    container.display_manager.override(providers.Object(display_manager_mock))
    container.mode_manager.override(providers.Object(mode_manager_mock))
    container.buttons_led_controller.override(providers.Factory(MagicMock))  # Correct Override
    container.rotary_control.override(providers.Object(rotary_control_mock))
    container.clock.override(providers.Object(clock_mock))
    container.playback_manager.override(providers.Object(playback_manager_mock))
    container.menu_manager.override(providers.Object(menu_manager_mock))
    container.playlist_manager.override(providers.Object(playlist_manager_mock))
    container.radio_manager.override(providers.Object(radio_manager_mock))
    container.tidal_manager.override(providers.Object(tidal_manager_mock))
    container.qobuz_manager.override(providers.Object(qobuz_manager_mock))
    container.state_handler.override(providers.Object(state_handler_mock))

    # Initialize resources
    container.init_resources()

    return container

def test_buttons_led_controller_factory(container):
    controller1 = container.buttons_led_controller()
    controller2 = container.buttons_led_controller()
    assert controller1 is not controller2, "ButtonsLEDController should be a factory and return new instances"
