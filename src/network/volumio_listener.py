# src/network/volumio_listener.py
import socketio
import requests
import threading
import logging
from blinker import Signal

class VolumioListener:
    def __init__(self, host='localhost', port=3000):
        self.host = host
        self.port = port
        self.socketIO = socketio.Client(logger=True, engineio_logger=True, reconnection=True)
        self.connect()

        # Define signals
        self.state_changed = Signal('state_changed')
        self.playlists_received = Signal('playlists_received')  # For generic playlists
        self.webradio_received = Signal('webradio_received')
        self.tidal_playlists_received = Signal('tidal_playlists_received')
        self.qobuz_playlists_received = Signal('qobuz_playlists_received')
        self.track_changed = Signal('track_changed')  # New signal for track updates

        self.register_socketio_events()

    def register_socketio_events(self):
        self.socketIO.on('connect', self.on_connect, namespace='/')
        self.socketIO.on('disconnect', self.on_disconnect, namespace='/')
        self.socketIO.on('pushState', self.on_push_state, namespace='/')
        self.socketIO.on('pushBrowseLibrary', self.on_push_browse_library, namespace='/')
        self.socketIO.on('pushTrack', self.on_push_track, namespace='/')  # New event for track updates

    def on_connect(self):
        logging.info("[VolumioListener] Connected to Volumio")
        self.socketIO.emit('getState', namespace='/')

    def on_disconnect(self):
        logging.warning("[VolumioListener] Disconnected from Volumio")

    def on_push_state(self, data):
        logging.debug("[VolumioListener] pushState received")
        self.state_changed.send(data)

    def on_push_browse_library(self, data):
        logging.debug("[VolumioListener] pushBrowseLibrary received")
        uri = data.get('uri', '')
        if 'playlists' in uri and 'tidal' not in uri and 'qobuz' not in uri:
            playlists = self.extract_playlists(data)
            self.playlists_received.send(playlists)
        elif 'webradio' in uri:
            webradio = self.extract_webradio(data)
            self.webradio_received.send(webradio)
        elif 'tidal' in uri:
            tidal_playlists = self.extract_playlists(data)
            self.tidal_playlists_received.send(tidal_playlists)
        elif 'qobuz' in uri:
            qobuz_playlists = self.extract_playlists(data)
            self.qobuz_playlists_received.send(qobuz_playlists)
        # Add other URI handlers as needed

    def on_push_track(self, data):
        logging.debug("[VolumioListener] pushTrack received")
        track_info = self.extract_track_info(data)
        self.track_changed.send(track_info)

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
                for item in radio_items if item['type'] == 'webradio'
            ]
        return []

    def extract_track_info(self, data):
        if 'track' in data:
            track = data['track']
            return {
                'title': track.get('title', 'Unknown Title'),
                'artist': track.get('artist', 'Unknown Artist'),
                'albumart': track.get('albumart', ''),
                'uri': track.get('uri', '')
            }
        return {}

    def connect(self):
        def listener_thread():
            try:
                self.socketIO.connect(f"http://{self.host}:{self.port}", namespaces=['/'])
                self.socketIO.wait()
            except socketio.exceptions.ConnectionError as e:
                logging.error(f"VolumioListener Connection Error: {e}")

        threading.Thread(target=listener_thread, daemon=True).start()

    def fetch_playlists(self):
        if self.socketIO.connected:
            self.socketIO.emit('browseLibrary', {'uri': 'playlists'}, namespace='/')
        else:
            logging.warning("Cannot fetch playlists - not connected.")

    def fetch_webradio_stations(self, uri="mywebradio"):
        if self.socketIO.connected:
            self.socketIO.emit('browseLibrary', {'uri': uri}, namespace='/')
        else:
            logging.warning("Cannot fetch webradio stations - not connected.")

    def fetch_tidal_playlists(self):
        if self.socketIO.connected:
            self.socketIO.emit('browseLibrary', {'uri': 'tidal'}, namespace='/')
        else:
            logging.warning("Cannot fetch Tidal playlists - not connected.")

    def fetch_qobuz_playlists(self):
        if self.socketIO.connected:
            self.socketIO.emit('browseLibrary', {'uri': 'qobuz'}, namespace='/')
        else:
            logging.warning("Cannot fetch Qobuz playlists - not connected.")

    def play_playlist(self, playlist_name):
        """Sends a request to Volumio to play a specific playlist."""
        if self.socketIO.connected:
            logging.info(f"Attempting to play playlist: {playlist_name}")
            self.socketIO.emit('playPlaylist', {'name': playlist_name}, namespace='/')
            logging.debug(f"'playPlaylist' event emitted with playlist: {playlist_name}")
        else:
            logging.warning(f"Cannot play playlist '{playlist_name}' - not connected to Volumio.")

    def play_webradio_station(self, title, uri):
        """Attempts to play a specific webradio station based on title match."""
        if self.socketIO.connected:
            logging.info(f"Attempting to play webradio station: {title}")
            self.socketIO.emit('replaceAndPlay', {
                "service": "webradio",
                "type": "webradio",
                "title": title,
                "uri": uri
            }, namespace='/')
            logging.debug(f"'replaceAndPlay' event emitted for webradio: {title}")
        else:
            logging.warning(f"Cannot play webradio station '{title}' - not connected to Volumio.")

    def play_tidal_playlist(self, title, uri):
        """Attempts to play a specific Tidal playlist."""
        if self.socketIO.connected:
            logging.info(f"Attempting to play Tidal playlist: {title}")
            self.socketIO.emit('replaceAndPlay', {
                "service": "tidal",
                "type": "playlist",
                "title": title,
                "uri": uri
            }, namespace='/')
            logging.debug(f"'replaceAndPlay' event emitted for Tidal playlist: {title}")
        else:
            logging.warning(f"Cannot play Tidal playlist '{title}' - not connected to Volumio.")

    def play_qobuz_playlist(self, title, uri):
        """Attempts to play a specific Qobuz playlist."""
        if self.socketIO.connected:
            logging.info(f"Attempting to play Qobuz playlist: {title}")
            self.socketIO.emit('replaceAndPlay', {
                "service": "qobuz",
                "type": "playlist",
                "title": title,
                "uri": uri
            }, namespace='/')
            logging.debug(f"'replaceAndPlay' event emitted for Qobuz playlist: {title}")
        else:
            logging.warning(f"Cannot play Qobuz playlist '{title}' - not connected to Volumio.")
