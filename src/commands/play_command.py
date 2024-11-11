# src/commands/play_command.py
from base_command import BaseCommand

class PlayCommand(BaseCommand):
    def __init__(self, volumio_listener):
        self.volumio_listener = volumio_listener

    def execute(self):
        self.volumio_listener.play()

