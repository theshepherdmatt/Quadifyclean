# src/managers/base_manager.py
from abc import ABC, abstractmethod
import logging

class BaseManager(ABC):
    def __init__(self, display_manager, volumio_listener, mode_manager):
        self.display_manager = display_manager
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        self.is_active = False
        self.on_mode_change_callbacks = []

        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or adjust as needed

    @abstractmethod
    def start_mode(self):
        pass

    @abstractmethod
    def stop_mode(self):
        pass

    def add_on_mode_change_callback(self, callback):
        if callable(callback):
            self.on_mode_change_callbacks.append(callback)
            self.logger.debug(f"Added mode change callback: {callback}")
        else:
            self.logger.warning(f"Attempted to add a non-callable callback: {callback}")

    def notify_mode_change(self, mode):
        self.logger.debug(f"Notifying mode change to: {mode}")
        for callback in self.on_mode_change_callbacks:
            try:
                callback(mode)
                self.logger.debug(f"Successfully executed callback: {callback}")
            except Exception as e:
                self.logger.error(f"Error in callback {callback}: {e}")

    def clear_display(self):
        self.display_manager.clear_screen()
        self.logger.info("Cleared the display screen.")
