# src/handlers/state_handler.py
import threading

class StateHandler:
    def __init__(self, volumio_listener, mode_manager):
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        self.register_listeners()

    def register_listeners(self):
        self.volumio_listener.register_state_change_callback(self.handle_state_change)

    def handle_state_change(self, state):
        threading.Thread(target=self.mode_manager.process_state_change, args=(state,)).start()

