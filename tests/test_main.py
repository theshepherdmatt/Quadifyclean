import pytest
from unittest.mock import MagicMock, patch
import logging
from src.main import main

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_container():
    # Create a mock container
    container = MagicMock()

    # Mock display_manager and its methods
    container.display_manager = MagicMock()
    container.display_manager.startup_sequence = MagicMock()

    # Mock VolumioListener and other components as needed
    container.volumio_listener = MagicMock()
    container.mode_manager = MagicMock()
    container.menu_manager = MagicMock()
    container.playlist_manager = MagicMock()
    container.radio_manager = MagicMock()
    container.tidal_manager = MagicMock()
    container.qobuz_manager = MagicMock()
    container.playback = MagicMock()
    container.rotary_control = MagicMock()
    container.button_led_controller = MagicMock()
    container.state_handler = MagicMock()
    container.config.from_yaml = MagicMock()

    return container

@patch('src.main.setup_logging')
@patch('src.main.atexit.register')
@patch('src.main.GPIO.cleanup')
@patch('src.main.time.sleep', side_effect=KeyboardInterrupt)  # Stop the infinite loop
@patch('src.main.VolumioListener', autospec=True)
def test_main(
    mock_volumio_listener,
    mock_sleep,
    mock_gpio_cleanup,
    mock_atexit_register,
    mock_setup_logging,
    mock_container  # Use the fixture here
):
    """Test the main function with mocked dependencies."""
    
    # Wire the mock container into the main function
    with patch('src.main.Container', return_value=mock_container):
        # Ensure mock_volumio_listener has proper signals mocked
        volumio_instance = mock_volumio_listener.return_value
        # Mock the connect method for each signal in VolumioListener
        for signal_name in [
            'state_changed', 'playlists_received', 'webradio_received',
            'tidal_playlists_received', 'qobuz_playlists_received', 'track_changed'
        ]:
            signal = getattr(volumio_instance, signal_name)
            signal.connect = MagicMock()

        # Run the main function
        try:
            main(container=mock_container)
        except KeyboardInterrupt:
            # Expected exit due to the `KeyboardInterrupt` in sleep
            pass

        # Assertions to check if initialization is done correctly
        mock_setup_logging.assert_called_once()
        mock_container.config.from_yaml.assert_called_once_with('config.yaml')

        # Check that startup_sequence or other display methods are called as expected
        mock_container.display_manager.startup_sequence.assert_called_once()

        # Verify that each signal's connect method was called once
        volumio_instance.state_changed.connect.assert_called_once()
        volumio_instance.playlists_received.connect.assert_called_once()
        volumio_instance.webradio_received.connect.assert_called_once()
        volumio_instance.tidal_playlists_received.connect.assert_called_once()
        volumio_instance.qobuz_playlists_received.connect.assert_called_once()
        volumio_instance.track_changed.connect.assert_called_once()
