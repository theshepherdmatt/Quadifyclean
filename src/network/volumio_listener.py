import socketio
import requests
import threading
import logging
from PIL import Image
import time

# Enable detailed logging for debugging
logging.basicConfig(level=logging.CRITICAL)

class VolumioListener:
    def __init__(self, host='localhost', port=3000, on_state_change_callback=None, oled=None, clock=None, mode_manager=None):
        self.host = host
        self.port = port
        self.on_state_change_callback = on_state_change_callback
        self.oled = oled
        self.clock = clock
        self.mode_manager = mode_manager
        
        # Initialize callback placeholders
        self.on_playlists_received_callback = None
        self.on_webradio_received_callback = None
        
        # Data storage
        self.playlists = []
        self.webradio_stations = []
        
        # Connection state
        self.connected = False

        # Initialize SocketIO connection and register event handlers
        self.socketIO = socketio.Client(logger=True, engineio_logger=True, reconnection=True)
        logging.debug(f"Connecting to Volumio WebSocket at {self.host}:{self.port}")
        self._register_socketio_events()

    def _register_socketio_events(self):
        """Sets up WebSocket event listeners for connection and data events."""
        self.socketIO.on('connect', self.on_connect, namespace='/')
        self.socketIO.on('disconnect', self.on_disconnect, namespace='/')
        self.socketIO.on('pushState', self.on_push_state, namespace='/')
        self.socketIO.on('pushQueue', self.on_push_queue, namespace='/')
        self.socketIO.on('pushBrowseLibrary', self.on_receive_browse_library, namespace='/')
        logging.debug("Registered WebSocket events.")

    def on_connect(self):
        logging.info("[WebSocket] Connected to Volumio")
        self.connected = True
        # Emit 'getState' here if needed
        self.socketIO.emit('getState', namespace='/')

    def on_disconnect(self):
        logging.warning("[WebSocket] Disconnected from Volumio")
        self.connected = False

    def get_volumio_state(self):
        """Fetches the current Volumio state."""
        try:
            response = requests.get(f"http://{self.host}:{self.port}/api/v1/getState")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching Volumio state: {e}")
            return None

    def fetch_playlists(self):
        """Requests playlists from Volumio."""
        if self.connected:
            logging.info("Fetching playlists from Volumio...")
            self.socketIO.emit('browseLibrary', {'uri': 'playlists'})
        else:
            logging.warning("Cannot fetch playlists - not connected to Volumio.")

    def fetch_webradio_stations(self, uri="mywebradio"):
        """Requests webradio stations from Volumio."""
        if self.connected:
            logging.info(f"Fetching webradio stations from Volumio for URI: {uri}")
            self.socketIO.emit('browseLibrary', {'uri': uri})
        else:
            logging.warning("Cannot fetch webradio stations - not connected to Volumio.")

    def register_playlists_callback(self, callback):
        """Registers a callback to be triggered when playlists are received."""
        self.on_playlists_received_callback = callback
        logging.debug("Registered playlists callback.")

    def register_webradio_callback(self, callback):
        """Registers a callback to be triggered when webradio stations are received."""
        self.on_webradio_received_callback = callback
        logging.debug("Registered webradio callback.")

    def on_receive_playlists(self, data):
        """Processes and stores received playlist data, then triggers the callback."""
        if 'navigation' in data and 'lists' in data['navigation']:
            playlists = data['navigation']['lists'][0].get('items', [])
            self.playlists = [{'title': item['title'], 'uri': item['uri']} for item in playlists if 'title' in item and 'uri' in item]
            logging.info(f"Playlists received: {[playlist['title'] for playlist in self.playlists]}")
            if self.on_playlists_received_callback:
                self.on_playlists_received_callback(self.playlists)
        else:
            logging.error("No playlists found in the received data.")

    def on_receive_radio(self, data):
        """Processes and stores received webradio data, then triggers the callback."""
        if 'navigation' in data and 'lists' in data['navigation']:
            radio_items = data['navigation']['lists'][0].get('items', [])
            self.webradio_stations = [
                {
                    'title': item['title'],
                    'uri': item['uri'],
                    'albumart': item.get('albumart', ''),
                    'bitrate': item.get('bitrate', 0)
                }
                for item in radio_items if item['type'] == 'webradio'
            ]
            logging.info(f"Radio stations received: {[station['title'] for station in self.webradio_stations]}")
            if self.on_webradio_received_callback:
                self.on_webradio_received_callback(self.webradio_stations)
        else:
            logging.warning("No radio stations found.")

    def on_receive_browse_library(self, data):
        if 'navigation' in data and 'lists' in data['navigation']:
            items = data['navigation']['lists'][0].get('items', [])
            playlists, webradio = [], []
            for item in items:
                item_type = item.get('type')
                if item_type == "playlist":
                    playlists.append({'title': item.get('title', ''), 'uri': item.get('uri', '')})
                elif item_type in ['webradio', 'mywebradio']:
                    webradio.append({
                        'title': item.get('title', ''),
                        'uri': item.get('uri', ''),
                        'albumart': item.get('albumart', ''),
                        'bitrate': item.get('bitrate', 0)
                    })

            # Assign and callback
            self.playlists = playlists if playlists else self.playlists
            self.webradio_stations = webradio if webradio else self.webradio_stations
            if self.on_playlists_received_callback and playlists:
                self.on_playlists_received_callback(self.playlists)
            if self.on_webradio_received_callback and webradio:
                self.on_webradio_received_callback(self.webradio_stations)
        else:
            logging.error("Invalid browseLibrary data received.")

    def play_playlist(self, playlist_name):
        """Sends a request to Volumio to play a specific playlist."""
        if self.connected:
            logging.info(f"Attempting to play playlist: {playlist_name}")
            self.socketIO.emit('playPlaylist', {'name': playlist_name})
            logging.debug(f"'playPlaylist' event emitted with playlist: {playlist_name}")
        else:
            logging.warning(f"Cannot play playlist '{playlist_name}' - not connected to Volumio.")

    def play_webradio_station(self, title, uri):
        """Attempts to play a specific webradio station based on title match."""
        if self.connected:
            normalized_title = title.strip().lower()
            for station in self.webradio_stations:
                if normalized_title in station.get('title', '').strip().lower():
                    logging.info(f"Playing webradio station '{station.get('title')}' with URI: {station.get('uri')}")
                    self.socketIO.emit('replaceAndPlay', {
                        "service": "webradio",
                        "type": "webradio",
                        "title": station.get('title'),
                        "uri": station.get('uri')
                    })
                    return
            logging.error(f"Webradio station '{title}' not found.")
        else:
            logging.warning(f"Cannot play webradio station '{title}' - not connected to Volumio.")

    def connect(self):
        """Starts the Volumio listener in a separate thread."""
        def listener_thread():
            attempt = 0
            while attempt < 5:  # Set a maximum retry limit
                try:
                    logging.debug("Attempting to connect to Volumio WebSocket...")
                    # Removing the forced 'websocket' transport for older compatibility
                    self.socketIO.connect(f"http://{self.host}:{self.port}", transports=['websocket'], namespaces=['/'])
                    logging.info("Connected to Volumio WebSocket, now listening...")
                    self.socketIO.emit('getState', namespace='/')
                    self.socketIO.wait()  # Keeps waiting for further events.
                    break  # Exit loop once connected
                except socketio.exceptions.ConnectionError as e:
                    attempt += 1
                    logging.error(f"Connection attempt {attempt} failed: {e}")
                    time.sleep(2)  # Wait before retrying

        threading.Thread(target=listener_thread, daemon=True).start()

    def on_push_state(self, data):
        if self.on_state_change_callback:
            logging.debug("State changed event received.")
            self.on_state_change_callback(data)

    def on_push_queue(self, data):
        """Handles Volumio 'pushQueue' events (placeholder)."""
        logging.debug("Queue event received but not processed.")

# Example test code to use VolumioListener
if __name__ == "__main__":
    def on_state_change(data):
        print("[Test] State changed:", data)

    def on_playlists_received(playlists):
        print("[Test] Playlists received:", playlists)

    def on_webradio_received(stations):
        print("[Test] Webradio stations received:", stations)

    # Initialize the VolumioListener with test callbacks
    listener = VolumioListener(
        host='localhost',  # Ensure this is set to your Volumio server's IP
        port=3000,
        on_state_change_callback=on_state_change
    )

    # Register additional callbacks
    listener.register_playlists_callback(on_playlists_received)
    listener.register_webradio_callback(on_webradio_received)

    # Connect and listen
    listener.connect()

    # Test: Fetch playlists and webradio stations
    listener.fetch_playlists()  # Check console to verify playlists are received
    listener.fetch_webradio_stations()  # Check console to verify webradio data
