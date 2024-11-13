import time
import logging
from src.network.volumio_listener import VolumioListener

# Set up logging to display debug information
logging.basicConfig(level=logging.DEBUG)

# Initialize the VolumioListener instance
volumio_listener = VolumioListener()

# Helper function to listen for various signals
def setup_signal_listeners():
    volumio_listener.state_changed.connect(lambda sender, state: print(f"State changed: {state}"))
    volumio_listener.playlists_received.connect(lambda sender, playlists: print(f"Playlists received: {playlists}"))
    volumio_listener.webradio_received.connect(lambda sender, stations: print(f"Webradio stations received: {stations}"))
    volumio_listener.tidal_playlists_received.connect(lambda sender, playlists: print(f"Tidal playlists received: {playlists}"))
    volumio_listener.qobuz_playlists_received.connect(lambda sender, playlists: print(f"Qobuz playlists received: {playlists}"))
    volumio_listener.track_changed.connect(lambda sender, track_info: print(f"Track changed: {track_info}"))

# Set up signal listeners to capture and print events
setup_signal_listeners()

# Test functions
def test_volumio_listener():
    # Wait for initial connection
    time.sleep(2)

    # Fetch and display general playlists
    print("\nFetching general playlists...")
    volumio_listener.fetch_playlists()
    time.sleep(3)  # Wait for response

    # Fetch and display webradio stations
    print("\nFetching webradio stations...")
    volumio_listener.fetch_webradio_stations()
    time.sleep(3)  # Wait for response

    # Fetch and display Tidal playlists
    print("\nFetching Tidal playlists...")
    volumio_listener.fetch_tidal_playlists()
    time.sleep(3)  # Wait for response

    # Fetch and display Qobuz playlists
    print("\nFetching Qobuz playlists...")
    volumio_listener.fetch_qobuz_playlists()
    time.sleep(3)  # Wait for response

    # Test playing items from each category
    print("\nAttempting to play specific items (examples)...")
    time.sleep(1)

    # Play a sample playlist if available
    sample_playlist = "Your Playlist Name Here"  # Replace with a valid playlist name
    print(f"Playing playlist: {sample_playlist}")
    volumio_listener.play_playlist(sample_playlist)
    time.sleep(3)

    # Play a sample webradio station if available
    sample_webradio = {"title": "Sample Radio", "uri": "webradio://sample_uri"}  # Replace with actual station data
    print(f"Playing webradio station: {sample_webradio['title']}")
    volumio_listener.play_webradio_station(sample_webradio['title'], sample_webradio['uri'])
    time.sleep(3)

    # Play a sample Tidal playlist if available
    sample_tidal = {"title": "Sample Tidal Playlist", "uri": "tidal://sample_uri"}  # Replace with actual Tidal playlist data
    print(f"Playing Tidal playlist: {sample_tidal['title']}")
    volumio_listener.play_tidal_playlist(sample_tidal['title'], sample_tidal['uri'])
    time.sleep(3)

    # Play a sample Qobuz playlist if available
    sample_qobuz = {"title": "Sample Qobuz Playlist", "uri": "qobuz://sample_uri"}  # Replace with actual Qobuz playlist data
    print(f"Playing Qobuz playlist: {sample_qobuz['title']}")
    volumio_listener.play_qobuz_playlist(sample_qobuz['title'], sample_qobuz['uri'])
    time.sleep(3)

# Run the test
test_volumio_listener()

