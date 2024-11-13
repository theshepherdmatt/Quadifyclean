# src/network/volumio_listener.py

import socketio
import requests
import threading
import logging
import time
from blinker import Signal

class VolumioListener:
    def __init__(self, host='localhost', port=3000, reconnect_delay=5):
        """
        Initialize VolumioListener to interact with Volumio's API.
        
        Parameters:
        - host (str): Host address for Volumio.
        - port (int): Port to connect to Volumio's SocketIO server.
        - reconnect_delay (int): Time to wait (in seconds) before attempting reconnection after a disconnect.
        """
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.socketIO = socketio.Client(logger=False, engineio_logger=False, reconnection=True)
        self.connected = Signal('connected')
        self.disconnected = Signal('disconnected')
        self.state_changed = Signal('state_changed')
        self.playlists_received = Signal('playlists_received')
        self.webradio_received = Signal('webradio_received')
        self.tidal_playlists_received = Signal('tidal_playlists_received')
        self.qobuz_playlists_received = Signal('qobuz_playlists_received')
        self.track_changed = Signal('track_changed')

        self.current_state = {}
        self.current_volume = 50

        self.register_socketio_events()
        self.connect()

    def register_socketio_events(self):
        """Register events to listen to from the SocketIO server."""
        self.socketIO.on('connect', self.on_connect)
        self.socketIO.on('disconnect', self.on_disconnect)
        self.socketIO.on('pushState', self.on_push_state)
        self.socketIO.on('pushBrowseLibrary', self.on_push_browse_library)
        self.socketIO.on('pushTrack', self.on_push_track)

    def on_connect(self):
        logging.info("[VolumioListener] Connected to Volumio.")
        self.connected.send()
        self.socketIO.emit('getState')

    def on_disconnect(self):
        logging.warning("[VolumioListener] Disconnected from Volumio. Attempting reconnection.")
        self.disconnected.send()
        self.schedule_reconnect()

    def schedule_reconnect(self):
        """Schedules a reconnection attempt after a delay."""
        time.sleep(self.reconnect_delay)
        if not self.socketIO.connected:
            self.connect()

    def on_push_state(self, data):
        logging.debug("[VolumioListener] Received pushState event.")
        self.current_state = data
        self.state_changed.send(state=data)

    def on_push_browse_library(self, data):
        logging.debug("[VolumioListener] Received pushBrowseLibrary event.")
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
        logging.debug("[VolumioListener] Received pushTrack event.")
        track_info = self.extract_track_info(data)
        self.track_changed.send(track_info=track_info)

    def extract_playlists(self, data):
        if 'navigation' in data and 'lists' in data['navigation']:
            playlists = data['navigation']['lists'][0].get('items', [])
            return [{'title': item['title'], 'uri': item['uri']} for item in playlists if 'title' in item and 'uri' in item]
        return []

    def extract_webradio(self, data):
        if 'navigation' in data and 'lists' in data['navigation']:
            radio_items = data['navigation']['lists'][0].get('items', [])
            return [
                {
                    'title': item['title'],
                    'uri': item['uri'],
                    'albumart': item.get('albumart', ''),
                    'bitrate': item.get('bitrate', 0)
                }
                for item in radio_items if item.get('type') == 'webradio'
            ]
        return []

    def extract_track_info(self, data):
        track = data.get('track', {})
        return {
            'title': track.get('title', 'Unknown Title'),
            'artist': track.get('artist', 'Unknown Artist'),
            'albumart': track.get('albumart', ''),
            'uri': track.get('uri', '')
        }

    def connect(self):
        """Attempts to connect to the Volumio SocketIO server."""
        try:
            self.socketIO.connect(f"http://{self.host}:{self.port}")
            self.socketIO.wait()  # Keep the listener active
        except Exception as e:
            logging.error(f"VolumioListener connection error: {e}")
            self.schedule_reconnect()

    def fetch_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'playlists'}, "fetch playlists")

    def fetch_webradio_stations(self, uri="radio/myWebRadio"):
        self._emit_with_check('browseLibrary', {'uri': uri}, "fetch webradio stations")

    def fetch_tidal_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'tidal'}, "fetch Tidal playlists")

    def fetch_qobuz_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'qobuz'}, "fetch Qobuz playlists")

    def play_playlist(self, playlist_name):
        """Sends a request to Volumio to play a specific playlist."""
        self._emit_with_check('playPlaylist', {'name': playlist_name}, f"play playlist {playlist_name}")

    def play_webradio_station(self, title, uri):
        """Attempts to play a specific webradio station based on title match."""
        self._emit_with_check('replaceAndPlay', {
            "service": "webradio",
            "type": "webradio",
            "title": title,
            "uri": uri
        }, f"play webradio station {title}")

    def play_tidal_playlist(self, title, uri):
        """Attempts to play a specific Tidal playlist."""
        self._emit_with_check('replaceAndPlay', {
            "service": "tidal",
            "type": "playlist",
            "title": title,
            "uri": uri
        }, f"play Tidal playlist {title}")

    def play_qobuz_playlist(self, title, uri):
        """Attempts to play a specific Qobuz playlist."""
        self._emit_with_check('replaceAndPlay', {
            "service": "qobuz",
            "type": "playlist",
            "title": title,
            "uri": uri
        }, f"play Qobuz playlist {title}")

    def adjust_volume(self, increment):
        """Adjusts the volume by the specified increment."""
        if self.socketIO.connected:
            try:
                current_volume = int(self.current_state.get('volume', 50))
                new_volume = min(max(current_volume + increment, 0), 100)
                self.socketIO.emit('volume', new_volume)
                logging.info(f"Volume adjusted to {new_volume}%.")
            except ValueError as e:
                logging.error(f"Invalid volume value: {e}")
        else:
            logging.warning("Cannot adjust volume - not connected.")

    def get_current_state(self):
        return self.current_state

    @property
    def is_connected(self):
        """Check if the listener is connected to Volumio."""
        return self.socketIO.connected

    def _emit_with_check(self, event, data, action_description):
        """Emit an event with a connection check and descriptive logging."""
        if self.socketIO.connected:
            logging.info(f"Attempting to {action_description}.")
            self.socketIO.emit(event, data)
            logging.debug(f"'{event}' event emitted with data: {data}")
        else:
            logging.warning(f"Cannot {action_description} - not connected.")