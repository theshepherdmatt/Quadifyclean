# src/network/volumio_listener.py

import socketio
import logging
import time
import threading
from blinker import Signal

class VolumioListener:
    def __init__(self, host='localhost', port=3000, mode_manager=None, reconnect_delay=5):
        """
        Initialize the VolumioListener.
        """
        self.logger = logging.getLogger("VolumioListener")
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("[VolumioListener] Initializing...")

        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.mode_manager = mode_manager
        self.socketIO = socketio.Client(logger=False, engineio_logger=False, reconnection=True)

        self.mode_manager = mode_manager

        # Define Blinker signals
        self.connected = Signal('connected')
        self.disconnected = Signal('disconnected')
        self.state_changed = Signal('state_changed')
        self.playlists_received = Signal('playlists_received')
        self.webradio_received = Signal('webradio_received')
        self.tidal_playlists_received = Signal('tidal_playlists_received')
        self.qobuz_playlists_received = Signal('qobuz_playlists_received')
        self.track_changed = Signal('track_changed')

        # Internal state
        self.current_state = {}
        self.current_volume = 50
        self._running = True
        self._reconnect_attempt = 1

        self.register_socketio_events()
        self.connect()

    def register_socketio_events(self):
        """Register events to listen to from the SocketIO server."""
        self.logger.info("[VolumioListener] Registering SocketIO events...")
        self.socketIO.on('connect', self.on_connect)
        self.socketIO.on('disconnect', self.on_disconnect)
        self.socketIO.on('pushState', self.on_push_state)
        self.socketIO.on('pushBrowseLibrary', self.on_push_browse_library)
        self.socketIO.on('pushTrack', self.on_push_track)

    def connect(self):
        """Connect to the Volumio server."""
        if self.socketIO.connected:
            self.logger.info("[VolumioListener] Already connected.")
            return
        try:
            self.logger.info(f"[VolumioListener] Connecting to Volumio at {self.host}:{self.port}...")
            self.socketIO.connect(f"http://{self.host}:{self.port}")
            self.logger.info("[VolumioListener] Successfully connected.")
        except Exception as e:
            self.logger.error(f"[VolumioListener] Connection error: {e}")
            self.schedule_reconnect()

    def on_connect(self):
        """Handle successful connection."""
        self.logger.info("[VolumioListener] Connected to Volumio.")
        self._reconnect_attempt = 1
        self.connected.send()
        self.socketIO.emit('getState')

    def is_connected(self):
        """Check if the client is connected to Volumio."""
        return self.socketIO.connected

    def on_disconnect(self):
        """Handle disconnection."""
        self.logger.warning("[VolumioListener] Disconnected from Volumio.")
        self.disconnected.send()
        self.schedule_reconnect()

    def schedule_reconnect(self):
        """Schedule a reconnection attempt."""
        delay = min(self.reconnect_delay * self._reconnect_attempt, 60)
        self.logger.info(f"[VolumioListener] Reconnecting in {delay} seconds...")
        threading.Thread(target=self._reconnect_after_delay, args=(self._reconnect_attempt,), daemon=True).start()

    def _reconnect_after_delay(self, attempt):
        time.sleep(attempt * self.reconnect_delay)
        if not self.socketIO.connected:
            self._reconnect_attempt += 1
            self.connect()

    def register_state_change_callback(self, callback):
        """Register a callback for state changes."""
        if callable(callback):
            self.state_changed.connect(callback)
            self.logger.debug(f"[VolumioListener] State change callback registered: {callback}")
        else:
            self.logger.warning("[VolumioListener] Provided callback is not callable.")


    def on_push_state(self, data):
        """Handle playback state changes."""
        self.logger.info("[VolumioListener] Received pushState event.")
        self.current_state = data
        self.logger.debug(f"Playback state: {data}")

        if self.mode_manager:
            self.mode_manager.process_state_change(data)

    def get_current_state(self):
        """
        Return the current state of the Volumio player.
        """
        return self.current_state
        
    def on_push_browse_library(self, data):
        """Handle 'pushBrowseLibrary' events."""
        self.logger.info("[VolumioListener] Received pushBrowseLibrary event.")
        uri = data.get('uri', '')
        if 'playlists' in uri and 'tidal' not in uri and 'qobuz' not in uri:
            playlists = self.extract_playlists(data)
            self.playlists_received.send(playlists=playlists)
        elif 'webradio' in uri:
            webradio = self.extract_webradio(data)
            self.webradio_received.send(stations=webradio)
        elif 'tidal' in uri:
            tidal_playlists = self.extract_playlists(data)
            self.tidal_playlists_received.send(playlists=tidal_playlists)
        elif 'qobuz' in uri:
            qobuz_playlists = self.extract_playlists(data)
            self.qobuz_playlists_received.send(playlists=qobuz_playlists)

    def on_push_track(self, data):
        """Handle 'pushTrack' events."""
        self.logger.info("[VolumioListener] Received pushTrack event.")
        track_info = self.extract_track_info(data)
        self.track_changed.send(track_info=track_info)

    def extract_playlists(self, data):
        """Extract playlist data."""
        if 'navigation' in data and 'lists' in data['navigation']:
            playlists = data['navigation']['lists'][0].get('items', [])
            return [{'title': item['title'], 'uri': item['uri']} for item in playlists if 'title' in item and 'uri' in item]
        return []

    def extract_webradio(self, data):
        """Extract webradio data."""
        if 'navigation' in data and 'lists' in data['navigation']:
            radio_items = data['navigation']['lists'][0].get('items', [])
            return [
                {'title': item['title'], 'uri': item['uri'], 'albumart': item.get('albumart', ''), 'bitrate': item.get('bitrate', 0)}
                for item in radio_items if item.get('type') == 'webradio'
            ]
        return []

    def extract_track_info(self, data):
        """Extract track info."""
        track = data.get('track', {})
        return {'title': track.get('title', 'Unknown Title'), 'artist': track.get('artist', 'Unknown Artist'), 'albumart': track.get('albumart', ''), 'uri': track.get('uri', '')}

    def fetch_playlists(self):
        """Fetch playlists."""
        self.socketIO.emit('browseLibrary', {'uri': 'playlists'})

    def fetch_webradio_stations(self, uri="radio/myWebRadio"):
        """Fetch webradio stations."""
        self.socketIO.emit('browseLibrary', {'uri': uri})

    def fetch_tidal_playlists(self):
        """Fetch Tidal playlists."""
        self.socketIO.emit('browseLibrary', {'uri': 'tidal'})

    def fetch_qobuz_playlists(self):
        """Fetch Qobuz playlists."""
        self.socketIO.emit('browseLibrary', {'uri': 'qobuz'})

    def play_playlist(self, playlist_name):
        """Play a specific playlist."""
        self.socketIO.emit('playPlaylist', {'name': playlist_name})

    def play_webradio_station(self, title, uri):
        """Play a specific webradio station."""
        self.socketIO.emit('replaceAndPlay', {'service': 'webradio', 'type': 'webradio', 'title': title, 'uri': uri})

    def play_tidal_playlist(self, title, uri):
        """Play a Tidal playlist."""
        self.socketIO.emit('replaceAndPlay', {'service': 'tidal', 'type': 'playlist', 'title': title, 'uri': uri})

    def play_qobuz_playlist(self, title, uri):
        """Play a Qobuz playlist."""
        self.socketIO.emit('replaceAndPlay', {'service': 'qobuz', 'type': 'playlist', 'title': title, 'uri': uri})

    def adjust_volume(self, increment):
        """Adjust volume."""
        try:
            current_volume = int(self.current_state.get('volume', 50))
            new_volume = min(max(current_volume + increment, 0), 100)
            self.socketIO.emit('volume', new_volume)
            self.logger.info(f"[VolumioListener] Volume adjusted to {new_volume}%.")
        except ValueError as e:
            self.logger.error(f"[VolumioListener] Invalid volume value: {e}")
