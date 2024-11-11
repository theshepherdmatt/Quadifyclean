# src/managers/mode_manager.py
from transitions import Machine
import threading

class ModeManager:
    states = ['clock', 'playback', 'menu', 'webradio', 'playlist', 'favourites', 'tidal']

    def __init__(self, display_manager, clock, playback, menu_manager, playlist_manager, radio_manager, tidal_manager):
        self.display_manager = display_manager
        self.clock = clock
        self.playback = playback
        self.menu_manager = menu_manager
        self.playlist_manager = playlist_manager
        self.radio_manager = radio_manager
        self.tidal_manager = tidal_manager

        self.machine = Machine(model=self, states=ModeManager.states, initial='clock')

        # Define transitions
        self.machine.add_transition(trigger='to_playback', source='*', dest='playback', before='enter_playback')
        self.machine.add_transition(trigger='to_menu', source='*', dest='menu', before='enter_menu')
        self.machine.add_transition(trigger='to_webradio', source='*', dest='webradio', before='enter_webradio')
        self.machine.add_transition(trigger='to_playlist', source='*', dest='playlist', before='enter_playlist')
        self.machine.add_transition(trigger='to_favourites', source='*', dest='favourites', before='enter_favourites')
        self.machine.add_transition(trigger='to_tidal', source='*', dest='tidal', before='enter_tidal')
        self.machine.add_transition(trigger='to_clock', source='*', dest='clock', before='enter_clock')

        self.on_mode_change_callbacks = []
        self.lock = threading.Lock()

    # Define enter methods
    def enter_playback(self):
        self.clock.stop()
        self.menu_manager.stop_mode()
        self.playback.start()
        self.notify_mode_change('playback')

    def enter_menu(self):
        self.clock.stop()
        self.playback.stop()
        self.menu_manager.start_mode()
        self.notify_mode_change('menu')

    def enter_webradio(self):
        self.clock.stop()
        self.playback.stop()
        self.radio_manager.start_mode()
        self.notify_mode_change('webradio')

    def enter_playlist(self):
        self.clock.stop()
        self.playback.stop()
        self.playlist_manager.start_mode()
        self.notify_mode_change('playlist')

    def enter_favourites(self):
        self.clock.stop()
        self.playback.stop()
        # Implement favourites mode
        self.notify_mode_change('favourites')

    def enter_tidal(self):
        self.clock.stop()
        self.playback.stop()
        self.tidal_manager.start_mode()
        self.notify_mode_change('tidal')

    def enter_clock(self):
        self.playback.stop()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.clock.start()
        self.notify_mode_change('clock')

    def process_state_change(self, state):
        status = state.get("status", "")
        if status == "play":
            self.to_playback()
        elif status in ["pause", "stop"]:
            self.to_clock()

    def add_on_mode_change_callback(self, callback):
        with self.lock:
            if callable(callback):
                self.on_mode_change_callbacks.append(callback)
                print(f"ModeManager: Added mode change callback: {callback}")

    def notify_mode_change(self, current_mode):
        with self.lock:
            for callback in self.on_mode_change_callbacks:
                try:
                    callback(current_mode)
                except Exception as e:
                    print(f"ModeManager: Error in callback {callback}: {e}")

    def get_mode(self):
        return self.state
