import unittest
from unittest.mock import MagicMock
from src.managers.qobuz_manager import QobuzManager

class TestQobuzManager(unittest.TestCase):
    def setUp(self):
        # Set up QobuzManager with mocked dependencies
        self.display_manager = MagicMock()
        self.volumio_listener = MagicMock()
        self.mode_manager = MagicMock()

        # Instantiate QobuzManager with mocks
        self.qobuz_manager = QobuzManager(
            display_manager=self.display_manager,
            volumio_listener=self.volumio_listener,
            mode_manager=self.mode_manager
        )

    def test_update_qobuz_playlists(self):
        # Mock playlist data
        mock_playlists = [
            {"title": "Chill Vibes", "uri": "qobuz:playlist:1"},
            {"title": "Top Hits", "uri": "qobuz:playlist:2"}
        ]
        
        # Call the method to update playlists
        self.qobuz_manager.update_qobuz_playlists(mock_playlists)

        # Explicitly call the method to display playlists if needed
        self.qobuz_manager.display_qobuz_playlists()

        # Check that the playlists have been updated correctly
        self.assertEqual(len(self.qobuz_manager.qobuz_playlists), 2)
        self.assertEqual(self.qobuz_manager.qobuz_playlists[0]["title"], "Chill Vibes")
        self.assertEqual(self.qobuz_manager.qobuz_playlists[1]["title"], "Top Hits")

        # Verify that the display manager's method was called to display the playlists
        self.display_manager.draw_custom.assert_called_once()

if __name__ == '__main__':
    unittest.main()
