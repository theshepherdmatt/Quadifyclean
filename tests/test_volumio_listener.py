import pytest
from unittest.mock import MagicMock, patch
from src.network.volumio_listener import VolumioListener

@pytest.fixture
def volumio_listener():
    """Fixture to initialize VolumioListener in test mode."""
    return VolumioListener(test_mode=True)


@patch('src.network.volumio_listener.socketio.Client')
def test_connect(mock_socket_client_class, volumio_listener):
    """Test that VolumioListener can successfully call connect on the socket client."""
    volumio_listener.test_mode = False  # Temporarily disable test mode for this test
    volumio_listener.socketIO = mock_socket_client_class.return_value

    # Call connect method
    volumio_listener.connect()

    # Assert connect method was called with the expected arguments
    volumio_listener.socketIO.connect.assert_called_once_with('http://localhost:3000')


@patch('src.network.volumio_listener.socketio.Client')
def test_emit_get_state(mock_socket_client_class, volumio_listener):
    """Test that the VolumioListener emits the 'getState' event upon connecting."""
    volumio_listener.test_mode = False
    volumio_listener.socketIO = mock_socket_client_class.return_value

    # Call connect and simulate on_connect
    volumio_listener.connect()
    volumio_listener.on_connect()

    # Verify that 'getState' event is emitted
    volumio_listener.socketIO.emit.assert_any_call("getState")


@patch('src.network.volumio_listener.socketio.Client')
def test_register_event_handlers(mock_socket_client_class, volumio_listener):
    """Test that VolumioListener registers the expected event handlers."""
    volumio_listener.test_mode = False
    volumio_listener.socketIO = mock_socket_client_class.return_value

    # Register events
    volumio_listener.register_socketio_events()

    # Ensure appropriate handlers are registered for events
    volumio_listener.socketIO.on.assert_any_call('connect', volumio_listener.on_connect)
    volumio_listener.socketIO.on.assert_any_call('disconnect', volumio_listener.on_disconnect)
    volumio_listener.socketIO.on.assert_any_call('pushState', volumio_listener.on_push_state)
    volumio_listener.socketIO.on.assert_any_call('pushBrowseLibrary', volumio_listener.on_push_browse_library)
    volumio_listener.socketIO.on.assert_any_call('pushTrack', volumio_listener.on_push_track)


def test_handle_push_state(volumio_listener):
    """Test the on_push_state method to ensure it triggers the state_changed signal."""
    mock_callback = MagicMock()
    volumio_listener.state_changed.connect(mock_callback)

    # Simulate a state change event
    test_state = {"status": "play", "artist": "Test Artist", "title": "Test Track"}
    volumio_listener.on_push_state(test_state)

    # Verify the callback was called with the test state
    mock_callback.assert_called_once_with(state=test_state)


def test_handle_push_browse_library(volumio_listener):
    """Test the on_push_browse_library method for playlist and webradio handling."""
    mock_playlists_callback = MagicMock()
    volumio_listener.playlists_received.connect(mock_playlists_callback)

    # Simulate a pushBrowseLibrary event for playlists
    test_data = {
        "uri": "playlists",
        "navigation": {"lists": [{"items": [{"title": "Test Playlist", "uri": "playlist_uri"}]}]}
    }
    volumio_listener.on_push_browse_library(test_data)

    # Verify that the playlists_received signal was emitted
    expected_playlists = [{"title": "Test Playlist", "uri": "playlist_uri"}]
    mock_playlists_callback.assert_called_once_with(playlists=expected_playlists)


def test_handle_push_track(volumio_listener):
    """Test that the on_push_track method triggers the track_changed signal."""
    mock_callback = MagicMock()
    volumio_listener.track_changed.connect(mock_callback)

    # Simulate a track change event
    test_data = {"track": {"title": "Track Title", "artist": "Artist Name", "uri": "track_uri"}}
    volumio_listener.on_push_track(test_data)

    # Verify the callback was called with the track information
    expected_track_info = {"title": "Track Title", "artist": "Artist Name", "albumart": "", "uri": "track_uri"}
    mock_callback.assert_called_once_with(track_info=expected_track_info)


def test_adjust_volume(volumio_listener):
    """Test that adjust_volume correctly emits a volume change event."""
    volumio_listener.socketIO = MagicMock()
    volumio_listener.current_state = {"volume": 50}

    # Adjust volume up by 10
    volumio_listener.adjust_volume(10)
    volumio_listener.socketIO.emit.assert_called_once_with("volume", 60)

    # Adjust volume down by 20
    volumio_listener.socketIO.reset_mock()
    volumio_listener.adjust_volume(-20)
    volumio_listener.socketIO.emit.assert_called_once_with("volume", 40)


def test_schedule_reconnect(volumio_listener):
    """Test that the schedule_reconnect method triggers a reconnect with backoff."""
    volumio_listener.socketIO = MagicMock()
    with patch("threading.Thread") as mock_thread:
        volumio_listener.schedule_reconnect()
        assert mock_thread.call_count == 1  # Ensures a reconnection thread is created


def test_stop_listener(volumio_listener):
    """Test that stop_listener stops the event loop and disconnects."""
    volumio_listener.socketIO = MagicMock()
    volumio_listener.stop_listener()

    # Ensure the _running flag is set to False and disconnect is called
    assert not volumio_listener._running
    volumio_listener.socketIO.disconnect.assert_called_once()


def test_play_webradio_station(volumio_listener):
    """Test play_webradio_station to ensure it emits the correct event for a station."""
    volumio_listener.socketIO = MagicMock()
    title, uri = "Test Station", "station_uri"
    volumio_listener.play_webradio_station(title, uri)

    # Verify the event emitted to play the webradio station
    expected_data = {
        "service": "webradio",
        "type": "webradio",
        "title": title,
        "uri": uri
    }
    volumio_listener.socketIO.emit.assert_called_once_with("replaceAndPlay", expected_data)


if __name__ == "__main__":
    pytest.main(["-v", "-s"])
