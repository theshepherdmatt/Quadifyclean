import pytest
from unittest.mock import MagicMock, patch, call
from src.network.volumio_listener import VolumioListener
from socketio import Client

@pytest.fixture
def volumio_listener():
    # Mock dependencies for VolumioListener
    mock_socket_client = MagicMock(spec=Client)
    return VolumioListener(socket_client=mock_socket_client)

@patch('src.network.volumio_listener.Client')
def test_connect(mock_socket_client_class, volumio_listener):
    """
    Test that the VolumioListener can successfully call connect on the socket client.
    """
    mock_socket_client_instance = mock_socket_client_class.return_value
    volumio_listener.connect()

    # Assert connect method was called with the expected arguments
    mock_socket_client_instance.connect.assert_called_once_with('http://localhost:3000', transports=['websocket'])
    print("test_connect: Success")

@patch('src.network.volumio_listener.Client')
def test_emit_get_state(mock_socket_client_class, volumio_listener):
    """
    Test that the VolumioListener emits the "getState" event upon connecting.
    """
    mock_socket_client_instance = mock_socket_client_class.return_value
    volumio_listener.connect()

    # Verify that the getState event is emitted
    mock_socket_client_instance.emit.assert_called_once_with("getState")
    print("test_emit_get_state: Success")

@patch('src.network.volumio_listener.Client')
def test_register_event_handlers(mock_socket_client_class, volumio_listener):
    """
    Test that VolumioListener registers the expected event handlers.
    """
    mock_socket_client_instance = mock_socket_client_class.return_value
    volumio_listener.connect()

    # Ensure appropriate handlers are registered for events
    expected_calls = [
        call('pushState', volumio_listener._handle_push_state),
        call('pushMultiRoomDevices', volumio_listener._handle_multi_room_devices),
        call('closeAllModals', volumio_listener._handle_close_all_modals)
    ]
    mock_socket_client_instance.on.assert_has_calls(expected_calls, any_order=True)
    print("test_register_event_handlers: Success")

def test_handle_push_state(volumio_listener):
    """
    Test the _handle_push_state method directly.
    """
    mock_callback = MagicMock()
    volumio_listener.state_changed.connect(mock_callback)

    # Simulate a state change
    test_state = {"status": "play", "artist": "Test Artist", "title": "Test Track"}
    volumio_listener._handle_push_state(test_state)

    # Verify the callback was invoked with correct state
    mock_callback.assert_called_once_with(test_state)
    print("test_handle_push_state: Success")

def test_handle_multi_room_devices(volumio_listener):
    """
    Test the _handle_multi_room_devices method directly.
    """
    mock_callback = MagicMock()
    volumio_listener.multi_room_devices_received.connect(mock_callback)

    # Simulate multi-room devices data
    test_devices = [{"name": "Room1", "host": "http://192.168.0.10"}]
    volumio_listener._handle_multi_room_devices(test_devices)

    # Verify the callback was invoked with correct devices list
    mock_callback.assert_called_once_with(test_devices)
    print("test_handle_multi_room_devices: Success")

def test_handle_close_all_modals(volumio_listener):
    """
    Test the _handle_close_all_modals method directly.
    """
    mock_callback = MagicMock()
    volumio_listener.close_all_modals.connect(mock_callback)

    # Simulate close all modals event
    volumio_listener._handle_close_all_modals()

    # Verify the callback was invoked
    mock_callback.assert_called_once()
    print("test_handle_close_all_modals: Success")

if __name__ == "__main__":
    pytest.main(["-v", "-s"])