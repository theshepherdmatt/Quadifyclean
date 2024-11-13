import pytest
from unittest.mock import MagicMock
from src.display.playback_manager import PlaybackManager

@pytest.fixture
def playback_manager():
    # Mock dependencies for PlaybackManager
    display_manager = MagicMock()
    volumio_listener = MagicMock()
    mode_manager = MagicMock()

    # Initialize PlaybackManager with mocks
    return PlaybackManager(
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=mode_manager
    )

def test_start_mode(playback_manager):
    """Test that start_mode activates playback mode and displays the current track."""
    playback_manager.start_mode()
    assert playback_manager.is_active is True
    playback_manager.display_manager.draw_custom.assert_called_once()

def test_stop_mode(playback_manager):
    """Test that stop_mode deactivates playback mode and clears the display."""
    playback_manager.start_mode()  # Activate mode first
    playback_manager.stop_mode()
    assert playback_manager.is_active is False
    try:
        playback_manager.display_manager.clear_display.assert_called_once()
        print("clear_display successfully called in test_stop_mode.")
    except AssertionError:
        print("Failed: clear_display was not called as expected in test_stop_mode.")
        raise

def test_update_playback_state(playback_manager):
    """Test that update_playback_state starts or stops playback mode based on the state."""
    # Test starting playback
    mock_state = {"status": "play"}
    playback_manager.update_playback_state(mock_state)
    assert playback_manager.is_active is True
    playback_manager.display_manager.draw_custom.assert_called_once()

    # Test stopping playback
    mock_state = {"status": "pause"}
    playback_manager.update_playback_state(mock_state)
    assert playback_manager.is_active is False
    try:
        playback_manager.display_manager.clear_display.assert_called()
        print("clear_display successfully called in test_update_playback_state.")
    except AssertionError:
        print("Failed: clear_display was not called as expected in test_update_playback_state.")
        raise

def test_update_current_track(playback_manager):
    """Test that update_current_track updates the track information and displays it."""
    playback_manager.start_mode()  # Ensure mode is active
    mock_track_info = {"title": "Track 1", "artist": "Artist 1"}
    playback_manager.update_current_track(mock_track_info)
    assert playback_manager.current_track == mock_track_info
    playback_manager.display_manager.draw_custom.assert_called()

def test_toggle_play_pause(playback_manager):
    """Test toggling between play and pause states."""
    # Mock the current state to be "play"
    playback_manager.volumio_listener.get_current_state.return_value = {"status": "play"}
    playback_manager.toggle_play_pause()
    playback_manager.volumio_listener.pause.assert_called_once()

    # Mock the current state to be "pause"
    playback_manager.volumio_listener.get_current_state.return_value = {"status": "pause"}
    playback_manager.toggle_play_pause()
    playback_manager.volumio_listener.play.assert_called_once()

def test_skip_track(playback_manager):
    """Test skipping to the next track."""
    playback_manager.skip_track()
    playback_manager.volumio_listener.next_track.assert_called_once()

def test_previous_track(playback_manager):
    """Test going back to the previous track."""
    playback_manager.previous_track()
    playback_manager.volumio_listener.previous_track.assert_called_once()

def test_adjust_volume(playback_manager):
    """Test adjusting the volume by a specified increment."""
    # Mock current volume
    playback_manager.volumio_listener.get_volume.return_value = 50

    # Increase volume
    playback_manager.adjust_volume(increment=10)
    playback_manager.volumio_listener.set_volume.assert_called_with(60)

    # Decrease volume
    playback_manager.adjust_volume(increment=-20)
    playback_manager.volumio_listener.set_volume.assert_called_with(30)

def test_handle_mode_change(playback_manager):
    """Test that handle_mode_change starts or stops playback manager based on mode."""
    # When mode is "playback", start_mode should be called
    playback_manager.handle_mode_change("playback")
    assert playback_manager.is_active is True
    playback_manager.display_manager.draw_custom.assert_called()

    # When mode changes away from "playback", stop_mode should be called
    playback_manager.handle_mode_change("radio")
    assert playback_manager.is_active is False
    try:
        playback_manager.display_manager.clear_display.assert_called()
        print("clear_display successfully called in test_handle_mode_change.")
    except AssertionError:
        print("Failed: clear_display was not called as expected in test_handle_mode_change.")
        raise

