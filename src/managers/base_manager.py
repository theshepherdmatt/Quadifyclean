# src/managers/base_manager.py
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw

class BaseManager(ABC):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        self.display_manager = display_manager
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        self.is_active = False
        self.on_mode_change_callbacks = []

    @abstractmethod
    def start_mode(self):
        pass

    @abstractmethod
    def stop_mode(self):
        pass

    def add_on_mode_change_callback(self, callback):
        if callable(callback):
            self.on_mode_change_callbacks.append(callback)

    def notify_mode_change(self, mode):
        for callback in self.on_mode_change_callbacks:
            try:
                callback(mode)
            except Exception as e:
                print(f"BaseManager: Error in callback {callback}: {e}")

    def clear_display(self):
        self.display_manager.clear_screen()
