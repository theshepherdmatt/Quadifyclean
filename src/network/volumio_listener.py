# src/network/volumio_listener.py

import sys
sys.setrecursionlimit(1500)

import socketio
import logging
import time
from blinker import Signal
import threading

class VolumioListener:
    def __init__(self, host='localhost', port=3000, mode_manager=None, reconnect_delay=5):
        self.logger = logging.getLogger("VolumioListener")
        self.logger.setLevel(logging.DEBUG)  # Adjust as needed
        self.logger.debug("[VolumioListener] Initializing...")
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.mode_manager = mode_manager 
        self.socketIO = socketio.Client(logger=False, engineio_logger=False, reconnection=True)
        self.register_socketio_events()

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
        self._reconnect_attempt = 1  # Track reconnect attempts

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
        """Attempts to connect to the Volumio SocketIO server and starts event loop in a thread."""
        try:
            self.logger.info("[VolumioListener] Attempting to connect to Volumio...")
            self.socketIO.connect(f"http://{self.host}:{self.port}")
            threading.Thread(target=self._run_event_loop, daemon=True).start()
        except Exception as e:
            self.logger.error(f"[VolumioListener] Connection error: {e}")
            self.schedule_reconnect()

    def _run_event_loop(self):
        """Runs the event loop for non-blocking continuous listening."""
        while self._running:
            try:
                self.socketIO.sleep(0.1)  # Non-blocking event loop
            except Exception as e:
                self.logger.error(f"[VolumioListener] Error in event loop: {e}")
                self.schedule_reconnect()
                break

    def stop_listener(self):
        """Stops the event loop and disconnects gracefully."""
        self._running = False
        if self.socketIO.connected:
            self.socketIO.disconnect()
        self.logger.info("[VolumioListener] Stopped.")

    def on_connect(self):
        self.logger.info("[VolumioListener] Connected to Volumio.")
        self._reconnect_attempt = 1  # Reset attempts on successful connection
        self.connected.send()
        self.socketIO.emit('getState')

    def on_disconnect(self, *args, **kwargs):
        self.logger.warning("[VolumioListener] Disconnected from Volumio.")
        self.disconnected.send()
        self.schedule_reconnect()

    def schedule_reconnect(self):
        """Schedules a reconnection attempt with exponential backoff."""
        delay = min(self.reconnect_delay * self._reconnect_attempt, 60)
        self.logger.info(f"[VolumioListener] Reconnecting in {delay} seconds...")
        threading.Thread(target=self._reconnect_after_delay, args=(self._reconnect_attempt,), daemon=True).start()

    def _reconnect_after_delay(self, attempt):
        time.sleep(attempt * self.reconnect_delay)
        if not self.socketIO.connected:
            self._reconnect_attempt += 1
            self.connect()

    def register_state_change_callback(self, callback):
        """Register a callback to be executed when the state changes."""
        if callable(callback):
            self.state_changed.connect(callback)
            self.logger.debug(f"[VolumioListener] State change callback registered: {callback}")
        else:
            self.logger.warning("[VolumioListener] Provided callback is not callable.")

    def on_push_state(self, data):
        self.logger.info("[VolumioListener] Received pushState event.")
        self.current_state = data  # Store the current state

        # Notify mode manager, if set
        if self.mode_manager:
            self.mode_manager.process_state_change(data)
        else:
            self.logger.warning("ModeManager is not set on VolumioListener, ignoring state change.")

        # Notify registered callbacks through the state_changed signal
        self.state_changed.send(self, state=data)

    def on_push_browse_library(self, data):
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
        self.logger.info("[VolumioListener] Received pushTrack event.")
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

    def fetch_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'playlists'}, "fetch playlists")

    def fetch_webradio_stations(self, uri="radio/myWebRadio"):
        self._emit_with_check('browseLibrary', {'uri': uri}, "fetch webradio stations")

    def fetch_tidal_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'tidal'}, "fetch Tidal playlists")

    def fetch_qobuz_playlists(self):
        self._emit_with_check('browseLibrary', {'uri': 'qobuz'}, "fetch Qobuz playlists")

    def play_playlist(self, playlist_name):
        self._emit_with_check('playPlaylist', {'name': playlist_name}, f"play playlist {playlist_name}")

    def play_webradio_station(self, title, uri):
        self._emit_with_check('replaceAndPlay', {
            "service": "webradio",
            "type": "webradio",
            "title": title,
            "uri": uri
        }, f"play webradio station {title}")

    def play_tidal_playlist(self, title, uri):
        self._emit_with_check('replaceAndPlay', {
            "service": "tidal",
            "type": "playlist",
            "title": title,
            "uri": uri
        }, f"play Tidal playlist {title}")

    def play_qobuz_playlist(self, title, uri):
        self._emit_with_check('replaceAndPlay', {
            "service": "qobuz",
            "type": "playlist",
            "title": title,
            "uri": uri
        }, f"play Qobuz playlist {title}")

    def adjust_volume(self, increment):
        if self.socketIO.connected:
            try:
                current_volume = int(self.current_state.get('volume', 50))
                new_volume = min(max(current_volume + increment, 0), 100)
                self.socketIO.emit('volume', new_volume)
                self.logger.info(f"[VolumioListener] Volume adjusted to {new_volume}%.")
            except ValueError as e:
                self.logger.error(f"[VolumioListener] Invalid volume value: {e}")
        else:
            self.logger.warning("Cannot adjust volume - not connected.")

    def get_current_state(self):
        return self.current_state

    @property
    def is_connected(self):
        return self.socketIO.connected

    def _emit_with_check(self, event, data, action_description):
        if self.socketIO.connected:
            self.logger.info(f"[VolumioListener] Attempting to {action_description}.")
            self.socketIO.emit(event, data)
            self.logger.debug(f"[VolumioListener] '{event}' event emitted with data: {data}")
        else:
            self.logger.warning(f"[VolumioListener] Cannot {action_description} - not connected.")
