import json

from visual_sonar import VisualSonar


def test_logs_redact_short_numeric_and_nested_input(monkeypatch, tmp_path, capsys):
    path = tmp_path / "map.json"
    path.write_text(json.dumps({"meta": {"resolution": [1000, 1000]}, "fields": []}))
    monkeypatch.setattr("visual_sonar.pyautogui.size", lambda: (1000, 1000))
    bot = VisualSonar(str(path))
    monkeypatch.setattr(bot, "ensure_focus", lambda: None)
    inputs = {"password": "xy", "pin": 123456, "nested": {"secret": "payload"}}
    bot.run_automation(inputs, dry_run=True)
    output = capsys.readouterr().out
    for secret in ("xy", "123456", "payload"):
        assert secret not in output
    assert output.count("[REDACTED]") == 3
    assert inputs["nested"]["secret"] == "payload"
