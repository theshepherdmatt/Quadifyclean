import unittest
from unittest.mock import MagicMock
from src.managers.tidal_manager import TidalManager

class TestTidalManager(unittest.TestCase):
    def setUp(self):
        # Set up TidalManager with mocked dependencies
        self.display_manager = MagicMock()
        self.volumio_listener = MagicMock()
        self.mode_manager = MagicMock()

        # Instantiate TidalManager with mocks
        self.tidal_manager = TidalManager(
            display_manager=self.display_manager,
            volumio_listener=self.volumio_listener,
            mode_manager=self.mode_manager
        )

    def test_update_tidal_playlists(self):
        # Mock playlist data
        mock_playlists = [
            {"title": "Top Tracks", "uri": "tidal:playlist:1"},
            {"title": "Pop Hits", "uri": "tidal:playlist:2"}
        ]
        
        # Call the method to update playlists
        self.tidal_manager.update_tidal_playlists(mock_playlists)

        # Explicitly call the method to display playlists if needed
        self.tidal_manager.display_tidal_playlists()

        # Check that the playlists have been updated correctly
        self.assertEqual(len(self.tidal_manager.tidal_playlists), 2)
        self.assertEqual(self.tidal_manager.tidal_playlists[0]["title"], "Top Tracks")
        self.assertEqual(self.tidal_manager.tidal_playlists[1]["title"], "Pop Hits")

        # Verify that the display manager's method was called to display the playlists
        self.display_manager.draw_custom.assert_called_once()

if __name__ == '__main__':
    unittest.main()
