# Visual Sonar 🔊

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](visual_sonar.py)
[![OCR Tests](https://github.com/godhiraj-code/wvdautomation/actions/workflows/ocr-test.yml/badge.svg)](https://github.com/godhiraj-code/wvdautomation/actions/workflows/ocr-test.yml)

**Automate WVD/Citrix remote desktop sessions using Computer Vision** — no DOM access, no server agents, no licensing fees.

Visual Sonar "echolocates" form fields by pressing TAB and detecting visual focus changes. Works where Selenium and traditional RPA tools can't.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Visual Field Detection** | Detects fields by screen diff when focus changes |
| 📊 **Data-Driven Testing** | Run same test with multiple data sets (CSV/JSON) |
| 🔍 **OCR Text Extraction** | Extract text from screen (pytesseract/easyocr) |
| 🖥️ **WVD Simulator** | Test safely without real remote desktop |
| 🔒 **Secrets Scrubbing** | Passwords never appear in logs |
| 📸 **Step Screenshots** | Every action captured for debugging |
| ⚡ **DPI Aware** | Per-monitor scaling support |

---

## 🚀 Quick Start

### Option A: Install from PyPI (Recommended)
```powershell
pip install visual-sonar
```

Then use:
```powershell
visual-sonar map
visual-sonar run
visual-sonar --help
```

### Option B: Install from Source
```powershell
git clone https://github.com/godhiraj-code/wvdautomation.git
cd wvdautomation
pip install -e .
```

### 2. Map Your Form
```powershell
python visual_sonar.py map
```
Name fields as `name:type` (types: `text`, `click`, `toggle`, `dropdown`, `double_click`)

### 3. Create Input
```json
{
    "username": "jdoe@company.com",
    "password": "SecretPass123",
    "signin": true
}
```

### 4. Run
```powershell
python visual_sonar.py run
```

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `map` | Interactive field mapping |
| `run [file.json]` | Execute automation |
| `list` | Show available test cases |
| `batch <data.csv>` | Data-driven batch testing |
| `extract screen` | OCR extract from full screen |
| `extract region x y w h` | OCR extract from region |
| `help` | Show full help |

---

## 🧪 Testing Without Remote Desktop

Use the built-in simulator:

```powershell
# Terminal 1 - Start simulator
python wvd_simulator.py

# Terminal 2 - Map and run
python visual_sonar.py map
python visual_sonar.py run
```

---

## 📊 Data-Driven Testing

Run same test with multiple credentials:

**Create `test_cases/users.csv`:**
```csv
username,password,signin
user1@co.com,pass1,true
user2@co.com,pass2,true
```

**Run batch:**
```powershell
python visual_sonar.py batch test_cases/users.csv
```

---

## 🔍 OCR Text Extraction

```powershell
# Full screen
python visual_sonar.py extract screen

# Specific region
python visual_sonar.py extract region 100 200 300 50

# Verify text exists (for assertions)
python visual_sonar.py extract verify 100 200 300 50 "Success"
```

> **Note:** Requires `pip install pytesseract` + [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)

---

## 🛡️ Safety

- **Emergency Stop**: Move mouse to TOP-LEFT corner
- **FailSafe**: Always enabled by default
- **Secrets**: Never logged, always scrubbed
- **Screenshots**: Captured on every step

---

## 📁 Files

| File | Purpose | Git |
|------|---------|-----|
| `wvd_map.json` | Field coordinates | ✅ |
| `input.json` | Your secrets | ❌ |
| `test_cases/` | Test data files | ✅ |
| `*.png` | Debug screenshots | ❌ |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No map file" | Run `python visual_sonar.py map` first |
| "Screen Unstable" | WVD connection laggy, wait and retry |
| Wrong coordinates | Remap (resolution/DPI may have changed) |
| OCR not working | Install Tesseract-OCR software |

---

## 📖 Documentation

- [USER_GUIDE.md](USER_GUIDE.md) - Comprehensive beginner guide

---

## 📜 License

MIT © Visual Sonar Team
