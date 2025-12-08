import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from visual_sonar import VisualSonar

class TestVisualSonarRunner(unittest.TestCase):
    def setUp(self):
        self.bot = VisualSonar("test_run.json")
        # Create a dummy map
        self.dummy_map = {
            "meta": {"resolution": [1000, 1000], "dpi_scale": 1.0},
            "fields": [
                {"name": "user", "type": "text", "coords": [100, 100, 50, 20]}
            ]
        }
        with open("test_run.json", "w") as f:
            json.dump(self.dummy_map, f)

    def tearDown(self):
        if os.path.exists("test_run.json"):
            os.remove("test_run.json")

    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.size', return_value=[1000, 1000])
    @patch('builtins.print') # Suppress print
    def test_runner_execution_and_clamping(self, mock_print, mock_size, mock_write, mock_click):
        # Coordinates (900, 900) + Size (200, 200) -> Center (1000, 1000).
        # Bounds are 0-999. Should clamp to (999, 999).
        # Also test DPI scaling: Saved=1.0, Current=1.0 (from setUp default).
        # Let's override self.dpi_scale to 2.0 to test "multiply ratio"
        self.bot.dpi_scale = 2.0
        # If saved=1.0, and current=2.0, ratio=2.0
        # Coords (10, 10). Center (10+10, 10+10) = 20, 20.
        # Scaled = 40, 40.
        
        self.dummy_map["fields"].append(
             {"name": "clamp_test", "type": "click", "coords": [900, 900, 200, 200]}
        )
        self.dummy_map["fields"].append(
             {"name": "dpi_test", "type": "click", "coords": [10, 10, 20, 20]}
        )
        with open("test_run.json", "w") as f:
            json.dump(self.dummy_map, f)
            
        data = {"clamp_test": "val", "dpi_test": "val", "user": "val"}
        self.bot.ensure_focus = MagicMock()
        
        self.bot.run_automation(data, dry_run=False)
        
        # Check Calls
        # 1. clamp_test: Center (1000,1000) * ratio(2.0) = 2000, 2000. Clamped to (999, 999).
        # 2. dpi_test: Center (20, 20) * ratio(2.0) = 40, 40. Clamped to (40, 40).
        
        # Since we append to existing 'user' field in setUp, we expect 3 calls.
        # 'user': 125, 110. * 2.0 = 250, 220.
        
        # Verify specific calls were made
        expected_calls = [
            call(250, 220), # user
            call(999, 999), # clamp_test
            call(40, 40)    # dpi_test
        ]
        # Depending on sort order or list order. List order preserved.
        mock_click.assert_has_calls(expected_calls, any_order=True)

    @patch('pyautogui.click')
    @patch('pyautogui.size', return_value=[1000, 1000])
    def test_runner_secrets_scrubbing(self, mock_size, mock_click):
        data = {"user": "secret_password_123"}
        self.bot.ensure_focus = MagicMock()
        self.bot.dpi_scale = 1.0 # simpler
        
        with patch('builtins.print') as mock_print:
            self.bot.run_automation(data, dry_run=True)
            
            # Verify the secret didn't get printed
            args_list = mock_print.call_args_list
            found_secret = False
            for args, _ in args_list:
                for arg in args:
                    if "secret_password_123" in str(arg):
                        found_secret = True
            self.assertFalse(found_secret, "Secret password leaked in logs!")

if __name__ == '__main__':
    unittest.main()
