import pytest
from unittest.mock import MagicMock, patch
from src.main import main

@pytest.fixture
def mock_container():
    # Mocking Container components
    container = MagicMock()

    # Mocking volumio_listener signals with MagicMock
    container.volumio_listener = MagicMock()
    container.volumio_listener.state_changed = MagicMock()
    container.volumio_listener.state_changed.connect = MagicMock()
    container.volumio_listener.playlists_received = MagicMock()
    container.volumio_listener.playlists_received.connect = MagicMock()
    container.volumio_listener.webradio_received = MagicMock()
    container.volumio_listener.webradio_received.connect = MagicMock()
    container.volumio_listener.tidal_playlists_received = MagicMock()
    container.volumio_listener.tidal_playlists_received.connect = MagicMock()
    container.volumio_listener.qobuz_playlists_received = MagicMock()
    container.volumio_listener.qobuz_playlists_received.connect = MagicMock()
    container.volumio_listener.track_changed = MagicMock()
    container.volumio_listener.track_changed.connect = MagicMock()

    # Mocking other dependencies of Container
    container.command_invoker = MagicMock()
    container.config = MagicMock()
    container.oled_device = MagicMock()
    container.display_manager = MagicMock()
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
    mock_container
):
    """Test the main function with mocked dependencies."""

    # Wire the mock container into the main function
    with patch('src.main.Container', return_value=mock_container):
        # Ensure mock_volumio_listener has proper signals mocked
        volumio_instance = mock_volumio_listener.return_value
        volumio_instance.state_changed = MagicMock()
        volumio_instance.state_changed.connect = MagicMock()
        volumio_instance.playlists_received = MagicMock()
        volumio_instance.playlists_received.connect = MagicMock()
        volumio_instance.webradio_received = MagicMock()
        volumio_instance.webradio_received.connect = MagicMock()
        volumio_instance.tidal_playlists_received = MagicMock()
        volumio_instance.tidal_playlists_received.connect = MagicMock()
        volumio_instance.qobuz_playlists_received = MagicMock()
        volumio_instance.qobuz_playlists_received.connect = MagicMock()
        volumio_instance.track_changed = MagicMock()
        volumio_instance.track_changed.connect = MagicMock()

        # Add debug prints before running main to check that listeners are mocked correctly
        print(f"volumio_instance.state_changed: {volumio_instance.state_changed}")
        print(f"volumio_instance.state_changed.connect: {volumio_instance.state_changed.connect}")

        # Run the main function
        try:
            main(container=mock_container)
        except KeyboardInterrupt:
            # Expected exit due to the `KeyboardInterrupt` in sleep
            pass

        # Assertions to check if initialization is done correctly
        mock_setup_logging.assert_called_once()
        mock_container.config.from_yaml.assert_called_once_with('config.yaml')

        # Check that each manager/component was initialized and called correctly
        mock_container.oled_device.assert_called_once()
        mock_container.display_manager.assert_called_once()
        mock_container.volumio_listener.assert_called_once()
        mock_container.mode_manager.assert_called_once()
        mock_container.menu_manager.assert_called_once()
        mock_container.playlist_manager.assert_called_once()
        mock_container.radio_manager.assert_called_once()
        mock_container.tidal_manager.assert_called_once()
        mock_container.qobuz_manager.assert_called_once()
        mock_container.playback.assert_called_once()
        mock_container.rotary_control.assert_called_once()
        mock_container.button_led_controller.assert_called_once()
        mock_container.state_handler.assert_called_once()

        # Check that listeners are registered correctly
        try:
            volumio_instance.state_changed.connect.assert_called_once()
            volumio_instance.playlists_received.connect.assert_called_once()
            volumio_instance.webradio_received.connect.assert_called_once()
            volumio_instance.tidal_playlists_received.connect.assert_called_once()
            volumio_instance.qobuz_playlists_received.connect.assert_called_once()
            volumio_instance.track_changed.connect.assert_called_once()
        except AssertionError as e:
            print(f"Failed to call connect on a listener: {e}")
            raise

        # Check that callbacks are registered with the rotary control
        assert mock_container.rotary_control.rotation_callback is not None
        assert mock_container.rotary_control.button_callback is not None

        # Check that `cleanup()` was registered to `atexit`
        mock_atexit_register.assert_called_once()

        # Check that GPIO cleanup was called on exit
        mock_gpio_cleanup.assert_called_once()
