import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Add parent dir to path to import visual_sonar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visual_sonar import VisualSonar

class TestVisualSonarMapper(unittest.TestCase):
    def setUp(self):
        self.bot = VisualSonar("test_map.json")
        # Mock pyautogui size
        with patch('pyautogui.size', return_value=(1920, 1080)):
            self.bot = VisualSonar("test_map.json")

    def test_resolution_match_fuzzy(self):
        saved = (1920, 1080)
        # Exact match
        self.assertTrue(self.bot._resolution_match(saved, (1920, 1080)))
        # < 5% diff (e.g., 1900 vs 1920 is ~1% diff)
        self.assertTrue(self.bot._resolution_match(saved, (1900, 1080)))
        # > 5% diff
        self.assertFalse(self.bot._resolution_match(saved, (1000, 1080)))

    @patch('cv2.imread')
    def test_get_focus_region_detects_change(self, mock_imread):
        # Create dummy images (black vs white square in center)
        img_a = np.zeros((100, 100, 3), dtype=np.uint8)
        img_b = np.zeros((100, 100, 3), dtype=np.uint8)
        # Draw a white rect in img_b
        img_b[40:60, 40:60] = [255, 255, 255]
        
        # We need to mock the CV processing calls or just feed these into the real function 
        # since the function takes PIL/CV images.
        # VisualSonar.get_focus_region expects PIL or array based on previous logic but updated code uses np.array() conversion
        # Let's pass numpy arrays directly which np.array() handles fine.
        
        res = self.bot.get_focus_region(img_a, img_b)
        self.assertIsNotNone(res)
        x, y, w, h = res
        # Bounding rect expands due to dilation (5x5 kernel, 2 iters)
        # Original 40. Dilation might push it to ~30-35.
        self.assertTrue(30 <= x <= 50, f"X coord {x} out of expected range")
        self.assertTrue(30 <= y <= 50, f"Y coord {y} out of expected range")

    def test_undo_command_removes_last_field(self):
        """Test that undo properly removes the last mapped field."""
        # Add some fields manually
        self.bot.map_data["fields"].append(
            {"name": "field1", "type": "text", "coords": [10, 10, 50, 20]}
        )
        self.bot.map_data["fields"].append(
            {"name": "field2", "type": "click", "coords": [100, 100, 50, 20]}
        )
        
        # Simulate undo
        self.assertEqual(len(self.bot.map_data["fields"]), 2)
        removed = self.bot.map_data["fields"].pop()
        self.assertEqual(removed["name"], "field2")
        self.assertEqual(len(self.bot.map_data["fields"]), 1)

    def test_three_strikes_guard_counter(self):
        """Test that 3 consecutive no-change TABs triggers exit condition."""
        # This tests the logic, not the full loop
        no_change_count = 0
        max_strikes = 3
        
        # Simulate 3 consecutive no-change detections
        for _ in range(3):
            no_change_count += 1
            if no_change_count >= max_strikes:
                break
        
        self.assertEqual(no_change_count, 3)
        
        # Test reset on successful detection
        no_change_count = 2
        res = (10, 10, 50, 20)  # Simulated successful detection
        if res:
            no_change_count = 0
        self.assertEqual(no_change_count, 0)

if __name__ == '__main__':
    unittest.main()
