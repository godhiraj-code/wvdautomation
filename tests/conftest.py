"""Keep unit tests from modifying the developer's desktop or clipboard."""
from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def isolate_desktop(monkeypatch):
    import pyautogui
    import pygetwindow
    import pyperclip

    for name in ("click", "doubleClick", "hotkey", "press", "write", "screenshot"):
        monkeypatch.setattr(pyautogui, name, Mock())
    monkeypatch.setattr(pyperclip, "copy", Mock())
    monkeypatch.setattr(pygetwindow, "getWindowsWithTitle", Mock(return_value=[]))
