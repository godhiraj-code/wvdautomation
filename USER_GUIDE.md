# Visual Sonar - Complete User Guide

> **Your Friendly Guide to Automating Remote Desktop (WVD/Citrix) Without Losing Your Mind**

---

## 🎯 What is Visual Sonar?

Visual Sonar is a **screen automation tool** that works with Remote Desktop sessions where traditional automation tools fail. It uses **computer vision** to detect form fields by observing visual changes when you press TAB.

Think of it like a bat using echolocation—it "pings" the screen with TAB presses and detects where the focus indicator appears!

```
┌──────────────────────────────────────────────┐
│     YOUR COMPUTER                            │
│  ┌─────────────┐     ┌─────────────┐        │
│  │ Visual Sonar│────►│ WVD Window  │        │
│  │   (Python)  │     │ (Remote PC) │        │
│  └─────────────┘     └─────────────┘        │
│         │                                    │
│         ▼                                    │
│   wvd_map.json (saved coordinates)          │
└──────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

### 1. Install Python (3.8 or higher)
Download from [python.org](https://www.python.org/downloads/)

During installation, **check "Add Python to PATH"**!

### 2. Install Dependencies
Open Command Prompt or PowerShell and run:

```powershell
cd c:\wvd_automation
pip install -r requirements.txt
```

This installs:
- `opencv-python` - Computer vision for screen analysis
- `pyautogui` - Mouse/keyboard control
- `pygetwindow` - Window detection for DPI scaling
- `pyperclip` - Clipboard support for unicode text
- `cryptography` - Optional encrypted input storage

### 3. Your Setup Checklist
- [ ] WVD/Citrix Remote Desktop window open
- [ ] The login form or application visible
- [ ] Your screen resolution is consistent (don't change it mid-automation!)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Map Your Form Fields

```powershell
python visual_sonar.py map
```

**What happens:**
1. You'll be prompted to press Enter
2. The bot switches to your WVD window
3. It presses TAB and detects the field that gets focus
4. You name each field in the format: `name:type`

**Example mapping session:**
```
[0 mapped] Step 1 → Enter (or command): 
  > Switching focus back to WVD...
  > Screen Stabilized.
  🎯 Detected field at (450,320) size 200x30
  💡 Types: text | click | toggle | dropdown | double_click
  > Name (name:type) or 'skip': username:text
  ✅ Added: username (text)

[1 mapped] Step 2 → Enter (or command):
```

### Step 2: Create Your Input File

Create `input.json` in the same folder:

```json
{
    "username": "your.email@company.com",
    "password": "YourSecretPassword123",
    "submit": true
}
```

> ⚠️ **Security Note:** `input.json` is in `.gitignore` and will never be committed to version control!

### Step 3: Run the Automation

```powershell
python visual_sonar.py run
```

**The bot will:**
1. Load your saved map (`wvd_map.json`)
2. Load your input values (`input.json`)
3. Click each field and enter the corresponding value
4. Take screenshots of each step (saved as `step_*.png`)

---

## 📚 Field Types Explained

| Type | Use For | What It Does |
|------|---------|--------------|
| `text` | Input fields | Click → Select All → Clear → Paste value |
| `click` | Buttons, links | Just clicks the element |
| `toggle` | Checkboxes | Click → Press Space |
| `dropdown` | Select menus | Click → Type to filter OR arrow navigation |
| `double_click` | Desktop icons | Double-clicks the element |

### Dropdown Values

For dropdown fields in `input.json`, you have two options:

**Option A: Type to filter**
```json
{
    "country": "India"
}
```

**Option B: Arrow key navigation**
```json
{
    "country": "arrow:5"
}
```
This presses Home (to reset), then Down 5 times, then Enter.

---

## 🎮 Mapping Commands

While in mapping mode, you can type these commands instead of pressing Enter:

| Command | What It Does |
|---------|--------------|
| `exit` | Save map and quit |
| `list` | Show all mapped fields so far |
| `undo` | Remove the last mapped field |
| `back` | Press Shift+Tab to go back one field |
| `skip` | Ignore the current detected field |

**Example undo:**
```
[3 mapped] Step 4 → Enter (or command): undo
  ↩️  Undone: password (text)
[2 mapped] Step 4 → Enter (or command):
```

---

## 🖥️ WVD Simulator (Safe Testing)

Don't have access to a real Remote Desktop? Use the built-in simulator!

### Start the Simulator
**Terminal 1:**
```powershell
cd c:\wvd_automation
python wvd_simulator.py
```

This opens a fake "WVD Login" window with:
- Username field
- Password field  
- Domain dropdown
- Remember me checkbox
- Sign In / Cancel buttons
- **Action log** showing all inputs received

### Map and Test
**Terminal 2:**
```powershell
cd c:\wvd_automation
python visual_sonar.py map
```

1. Press Enter to start mapping
2. The bot will TAB through the simulator's fields
3. Name each field (e.g., `username:text`, `password:text`, `signin:click`)
4. Type `exit` to save

### Create Test Input
Create `input.json`:
```json
{
    "username": "test.user@example.com",
    "password": "TestPassword123",
    "signin": true
}
```

### Run Automation
```powershell
python visual_sonar.py run
```

Watch the simulator's **Action Log** to verify all inputs were received correctly!

---

## 🧪 Testing Your Setup

### 1. Run the Tests
```powershell
cd c:\wvd_automation
python -m pytest tests/ -v
```

Expected output:
```
tests/test_mapper.py::TestVisualSonarMapper::test_resolution_match_fuzzy PASSED
tests/test_mapper.py::TestVisualSonarMapper::test_get_focus_region_detects_change PASSED
tests/test_mapper.py::TestVisualSonarMapper::test_undo_command_removes_last_field PASSED
tests/test_mapper.py::TestVisualSonarMapper::test_three_strikes_guard_counter PASSED
tests/test_runner.py::TestVisualSonarRunner::test_runner_execution_and_clamping PASSED
tests/test_runner.py::TestVisualSonarRunner::test_runner_secrets_scrubbing PASSED
```

### 2. Dry Run (Safe Test)
Test without actually clicking anything:

```powershell
python -c "from visual_sonar import VisualSonar; bot = VisualSonar(); bot.run_automation({'username': 'test'}, dry_run=True)"
```

This prints what *would* happen without performing any actions.

### 3. Verify Your Map
Open `wvd_map.json` and check:
```json
{
    "meta": {
        "resolution": [1920, 1080],
        "dpi_scale": 1.0
    },
    "fields": [
        {
            "name": "username",
            "type": "text",
            "coords": [450, 320, 200, 30]
        }
    ]
}
```

---

## 🛡️ Safety Features

### Emergency Stop
**Move your mouse to the TOP-LEFT corner of the screen** at any time to immediately stop the automation. This is the PyAutoGUI failsafe.

### Pre-Run Checklist
Before executing, the bot shows you exactly what will happen:
```
┌─────────────────────────────────────┐
│   PRE-RUN CHECKLIST                 │
└─────────────────────────────────────┘
  Map: wvd_map.json (3 fields)
  Input: input.json (3 values)

  Fields to execute:
    ✓ username (text)
    ✓ password (text)
    ✓ submit (click)

  ⚠️  SAFETY: Move mouse to TOP-LEFT to abort!

Proceed? [y/N]:
```

### Error Recovery
If something goes wrong, the bot:
1. Takes a screenshot (`error_fieldname_timestamp.png`)
2. Stops execution
3. Shows you exactly which field failed

---

## 🔧 Troubleshooting

### "No visual change detected"
**Cause:** The field doesn't have a visible focus ring (border highlight).

**Fix:** 
- Some apps don't show focus indicators—try clicking manually first
- Ensure the WVD window is fully visible (not minimized or obscured)

### "Resolution mismatch warning"
**Cause:** Your screen resolution changed since mapping.

**Fix:**
- Re-map with current resolution, OR
- Accept the warning (the bot will try to scale coordinates)

### "DPI scaling issues"
**Cause:** Multi-monitor setups with different DPI settings.

**Fix:**
- Run mapping on the same monitor where you'll run automation
- Keep WVD window on your primary display

### "pyperclip not working"
**Cause:** Clipboard access issue.

**Fix (Windows):**
```powershell
pip install pyperclip
```

---

## 📁 File Reference

| File | Purpose | Version Control |
|------|---------|-----------------|
| `visual_sonar.py` | Main application | ✅ Commit |
| `wvd_map.json` | Saved field coordinates | ✅ Commit (per environment) |
| `input.json` | Runtime values (SECRETS!) | ❌ Never commit |
| `requirements.txt` | Python dependencies | ✅ Commit |
| `step_*.png` | Execution screenshots | ❌ Ignored |
| `error_*.png` | Error screenshots | ❌ Ignored |
| `last_debug.png` | Last detected field | ❌ Ignored |

---

## 🎓 Advanced Usage

### Running in CI/Docker (Headless)
Set the environment variable to skip GUI windows:
```powershell
$env:HEADLESS = "1"
python visual_sonar.py run
```

### Custom Detection Algorithm
Extend the `VisualSonar` class:
```python
class ColorSonar(VisualSonar):
    def get_focus_region(self, before, after):
        # Your custom HSV-based detection
        ...
```

### Encrypted Input File (Coming Soon)
The `cryptography` package is installed for future encrypted `input.json` support.

---

## 💡 Tips for Best Results

1. **Consistent Resolution** - Don't change screen resolution between mapping and running
2. **Stable Network** - Wait for RDP to fully render before starting
3. **Visible Focus Rings** - Choose apps/themes with clear focus indicators
4. **Test on Dev First** - Always map and test on a development environment
5. **Keep Mouse Away** - During mapping, don't move your mouse over the WVD window

---

## 📞 Getting Help

```powershell
python visual_sonar.py help
```

For issues, check `last_debug.png` to see what the bot detected, and `error_*.png` for failure states.

---

**Happy Automating! 🚀**
