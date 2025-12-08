"""
Visual Sonar - WVD/Citrix Remote Desktop Automation Tool

A computer vision-based GUI automation tool for automating remote desktop
sessions where DOM access is unavailable. Uses screen diff analysis to
detect form fields and pyautogui for interaction.

Usage:
    python visual_sonar.py map     - Interactive field mapping
    python visual_sonar.py run     - Execute automation
    python visual_sonar.py list    - List test cases
    python visual_sonar.py batch   - Data-driven batch testing
    python visual_sonar.py extract - OCR text extraction
    python visual_sonar.py help    - Show help

Author: Visual Sonar Team
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Visual Sonar Team"

# Standard library imports
import copy
import ctypes
import json
import os
import sys
import time

# Third-party imports
import cv2
import numpy as np
import pyautogui
import pyperclip
import pygetwindow as gw

# Platform-specific imports
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False  # Not on Windows

# Optional: Encryption support
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Optional: OCR support (try multiple backends)
OCR_BACKEND = None
try:
    import easyocr
    OCR_BACKEND = 'easyocr'
except ImportError:
    try:
        import pytesseract
        from PIL import Image
        OCR_BACKEND = 'pytesseract'
    except ImportError:
        OCR_BACKEND = None

# --- Configuration ---
pyautogui.FAILSAFE = True   # Move mouse to corner to abort
pyautogui.PAUSE = 0.05      # Small delay between actions

class VisualSonar:
    """
    Visual Sonar - Computer Vision GUI Automation for Remote Desktop.
    
    This class provides methods to:
    - Map form fields by detecting visual focus changes
    - Execute automation using saved coordinate maps
    - Extract text using OCR (easyocr or pytesseract)
    
    Example:
        >>> bot = VisualSonar()
        >>> bot.map_form()  # Interactive mapping
        >>> bot.run_automation({"username": "test", "password": "secret"})
    
    Attributes:
        output_file (str): Path to save/load field coordinate map
        dpi_scale (float): Current display DPI scale factor
        map_data (dict): Current field mapping with meta info
    """
    
    # Configuration constants
    MICRO_MOTION_LIMIT = 20        # Pixel change threshold for "stable"
    STABILIZATION_TIMEOUT = 5.0    # Max seconds to wait for stable screen
    STABLE_FRAMES_REQUIRED = 3     # Consecutive stable frames needed
    
    def __init__(self, output_file="wvd_map.json"):
        """
        Initialize Visual Sonar.
        
        Args:
            output_file: Path for saving/loading field coordinates (default: wvd_map.json)
        """
        self.output_file = output_file
        self.micro_motion_limit = self.MICRO_MOTION_LIMIT
        self.stabilization_timeout = self.STABILIZATION_TIMEOUT
        self.stable_frames_required = self.STABLE_FRAMES_REQUIRED
        
        # Get Real DPI Scale (Per-Monitor Fix)
        self.dpi_scale = self._detect_dpi_scale()
            
        self.map_data = {
            "meta": {
                "resolution": pyautogui.size(),
                "dpi_scale": self.dpi_scale,
                "version": __version__
            },
            "fields": []
        }
        print(f"Init: Res={self.map_data['meta']['resolution']}, DPI={self.dpi_scale:.2f}")
        
        # OCR Reader (lazy init for performance)
        self._ocr_reader = None
    
    def _detect_dpi_scale(self):
        """Detect DPI scale from RDP window or system."""
        dpi_scale = 1.0
        try:
            # Try to get DPI from actual RDP window if present
            rdp_windows = gw.getWindowsWithTitle('Remote Desktop')
            if rdp_windows:
                hwnd = rdp_windows[0]._hWnd
                dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
                dpi_scale = dpi / 96.0
        except Exception:
            # Fallback to system DPI
            try:
                dpi_scale = ctypes.windll.user32.GetDpiForSystem() / 96.0
            except Exception:
                pass
        return dpi_scale

    def _get_ocr_reader(self):
        """Lazy-load OCR reader."""
        if OCR_BACKEND is None:
            raise RuntimeError("No OCR backend available. Install easyocr or pytesseract.")
        if OCR_BACKEND == 'easyocr' and self._ocr_reader is None:
            print("  ⏳ Loading OCR models (first time may take a while)...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("  ✅ OCR ready.")
        return self._ocr_reader

    def extract_text_from_region(self, x, y, w, h, save_debug=True):
        """Extract text from a specific screen region using OCR."""
        if OCR_BACKEND is None:
            raise RuntimeError("No OCR backend. Install: pip install pytesseract (+ Tesseract-OCR)")
        
        # Capture screenshot of the region
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        img_array = np.array(screenshot)
        
        # Save debug image
        if save_debug:
            debug_path = f"ocr_region_{int(time.time())}.png"
            cv2.imwrite(debug_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
            print(f"  📸 Saved region to: {debug_path}")
        
        # Run OCR based on backend
        if OCR_BACKEND == 'easyocr':
            reader = self._get_ocr_reader()
            results = reader.readtext(img_array)
            extracted_texts = [text for (_, text, confidence) in results]
            return " ".join(extracted_texts), results
        else:  # pytesseract
            from PIL import Image
            pil_img = Image.fromarray(img_array)
            text = pytesseract.image_to_string(pil_img)
            # Return in similar format to easyocr
            return text.strip(), [("box", text.strip(), 0.9)]

    def extract_text_from_screen(self, save_debug=True):
        """Extract all text from the entire screen."""
        if OCR_BACKEND is None:
            raise RuntimeError("No OCR backend. Install: pip install pytesseract (+ Tesseract-OCR)")
        
        # Capture full screenshot
        screenshot = pyautogui.screenshot()
        img_array = np.array(screenshot)
        
        # Save debug image
        if save_debug:
            debug_path = f"ocr_fullscreen_{int(time.time())}.png"
            cv2.imwrite(debug_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
            print(f"  📸 Saved screenshot to: {debug_path}")
        
        # Run OCR based on backend
        if OCR_BACKEND == 'easyocr':
            reader = self._get_ocr_reader()
            results = reader.readtext(img_array)
            extracted_texts = [text for (_, text, confidence) in results]
            return " ".join(extracted_texts), results
        else:  # pytesseract
            from PIL import Image
            pil_img = Image.fromarray(img_array)
            text = pytesseract.image_to_string(pil_img)
            lines = [line for line in text.split('\n') if line.strip()]
            results = [("box", line, 0.9) for line in lines]
            return text.strip(), results

    def extract_text_from_field(self, field_name):
        """Extract text from a mapped field region."""
        if not os.path.exists(self.output_file):
            raise FileNotFoundError(f"Map file not found: {self.output_file}")
        
        with open(self.output_file, 'r') as f:
            data = json.load(f)
        
        # Find the field
        field = None
        for f_data in data["fields"]:
            if f_data["name"] == field_name:
                field = f_data
                break
        
        if not field:
            raise ValueError(f"Field '{field_name}' not found in map.")
        
        x, y, w, h = field["coords"]
        return self.extract_text_from_region(x, y, w, h)

    def verify_text_contains(self, region, expected_text, case_sensitive=False):
        """Verify that a region contains expected text. Returns True/False."""
        x, y, w, h = region
        extracted, _ = self.extract_text_from_region(x, y, w, h, save_debug=False)
        
        if case_sensitive:
            return expected_text in extracted
        else:
            return expected_text.lower() in extracted.lower()

    def ensure_focus(self):
        """Dance to ensure WVD window has focus."""
        print("  > Ensuring Focus (Alt+Tab dance)...")
        # Bring remote window to front (assuming it was last active)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        # Click center to focus the RDP session safely
        cx, cy = pyautogui.size()
        pyautogui.click(cx // 2, cy // 2)
        time.sleep(0.5)

    def wait_for_stabilization(self):
        """Adaptive Stabilization: Waits for N consecutive identical frames."""
        print("  ...waiting for screen quiescence...", end="\r")
        start_time = time.time()
        
        last_img = pyautogui.screenshot()
        last_gray = cv2.cvtColor(np.array(last_img), cv2.COLOR_RGB2GRAY)
        
        stable_count = 0
        
        while (time.time() - start_time) < self.stabilization_timeout:
            time.sleep(0.1)
            
            curr_img = pyautogui.screenshot()
            curr_gray = cv2.cvtColor(np.array(curr_img), cv2.COLOR_RGB2GRAY)
            
            diff = cv2.absdiff(last_gray, curr_gray)
            non_zero = cv2.countNonZero(diff)
            
            if non_zero < self.micro_motion_limit:
                stable_count += 1
                if stable_count >= self.stable_frames_required:
                    print("  > Screen Stabilized.             ")
                    return curr_img
            else:
                stable_count = 0 # Reset if movement detected
            
            last_gray = curr_gray
            
        print("  > WARNING: Screen Unstable (Lag/Animation). Proceeding.")
        return pyautogui.screenshot()

    def get_focus_region(self, img_before, img_after):
        """Diff with Dynamic Thresholding."""
        gray_a = cv2.cvtColor(np.array(img_before), cv2.COLOR_RGB2GRAY)
        gray_b = cv2.cvtColor(np.array(img_after), cv2.COLOR_RGB2GRAY)

        # Blur
        gray_a = cv2.GaussianBlur(gray_a, (5, 5), 0)
        gray_b = cv2.GaussianBlur(gray_b, (5, 5), 0)

        diff = cv2.absdiff(gray_a, gray_b)
        
        # Dynamic Threshold: Median + 15 to hide compression artifacts
        median_val = np.median(diff)
        thresh_val = int(median_val + 15)
        _, thresh = cv2.threshold(diff, thresh_val, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours: return None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 100: return None

        x, y, w, h = cv2.boundingRect(largest)
        
        debug = np.array(img_after)
        cv2.rectangle(debug, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imwrite("last_debug.png", cv2.cvtColor(debug, cv2.COLOR_RGB2BGR))
        
        return x, y, w, h

    def _beep(self, success=True):
        """Play sound feedback."""
        try:
            if success:
                winsound.Beep(800, 150)  # High pitch = detected
            else:
                winsound.Beep(300, 150)  # Low pitch = no detection
        except:
            pass  # Silently fail if no sound device

    def _list_fields(self):
        """Print all mapped fields so far."""
        if not self.map_data["fields"]:
            print("  📋 No fields mapped yet.")
        else:
            print(f"  📋 Mapped Fields ({len(self.map_data['fields'])}):")
            for i, f in enumerate(self.map_data["fields"], 1):
                print(f"     {i}. {f['name']} ({f['type']}) at ({f['coords'][0]},{f['coords'][1]})")

    def map_form(self):
        print("\n=== MAPPING MODE ===")
        print("Commands: 'exit' | 'list' | 'undo' | 'back' (Shift+Tab)")
        
        self.ensure_focus()
        
        step = 0
        no_change_count = 0
        try:
            while True:
                step += 1
                field_count = len(self.map_data["fields"])
                try:
                    c = input(f"\n[{field_count} mapped] Step {step} → Enter (or command): ").strip().lower()
                    
                    # Handle commands
                    if c == 'exit': 
                        break
                    elif c == 'list':
                        self._list_fields()
                        step -= 1  # Don't increment step for list
                        continue
                    elif c == 'undo':
                        if self.map_data["fields"]:
                            removed = self.map_data["fields"].pop()
                            print(f"  ↩️  Undone: {removed['name']} ({removed['type']})")
                        else:
                            print("  ⚠️  Nothing to undo.")
                        step -= 1
                        continue
                    elif c == 'back':
                        # Switch focus back to WVD and press Shift+Tab
                        print("  > Switching focus and pressing Shift+Tab...")
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(0.5)
                        pyautogui.hotkey('shift', 'tab')
                        time.sleep(0.3)
                        print("  ⬅️  Moved back one field.")
                        step -= 1
                        continue
                        
                except EOFError: break
                
                # Switch focus back to WVD
                print("  > Switching focus back to WVD...")
                pyautogui.hotkey('alt', 'tab')
                time.sleep(0.5)
                
                img_before = self.wait_for_stabilization()
                pyautogui.press('tab')
                img_after = self.wait_for_stabilization()
                
                res = self.get_focus_region(img_before, img_after)
                
                if res:
                    x, y, w, h = res
                    self._beep(True)  # Success sound
                    print(f"  🎯 Detected field at ({x},{y}) size {w}x{h}")
                    
                    # Show detected region
                    debug_img = cv2.imread("last_debug.png")
                    if debug_img is not None:
                        # Headless check for CI
                        if os.environ.get("HEADLESS", "0") == "0":
                            cv2.imshow("Field Detected (Focus Terminal to name)", debug_img)
                            cv2.waitKey(1)
                    
                    while True:
                        print("  💡 Types: text | click | toggle | dropdown | double_click")
                        u = input("  > Name (name:type) or 'skip': ").strip()
                        if u.lower() == 'skip': 
                            print("  ⏭️  Skipped.")
                            break
                        if ":" in u:
                            parts = u.split(":", 1)
                            if len(parts) == 2:
                                n, t = parts[0].strip(), parts[1].strip()
                                valid_types = ['text', 'click', 'toggle', 'dropdown', 'double_click']
                                if t not in valid_types:
                                    print(f"  ❌ Invalid type '{t}'. Use: {', '.join(valid_types)}")
                                    continue
                                self.map_data["fields"].append({
                                    "name": n,
                                    "type": t,
                                    "coords": [x, y, w, h]
                                })
                                print(f"  ✅ Added: {n} ({t})")
                                break
                        print("  ❌ Format: name:type (e.g., 'username:text')")
                    if os.environ.get("HEADLESS", "0") == "0":
                        cv2.destroyAllWindows()
                else:
                    self._beep(False)  # Fail sound
                    print("  ⚠️  No visual change. (No focus ring?)")
                    
                    # 3-Strikes Guard
                    no_change_count += 1
                    if no_change_count >= 3:
                        print("\n⛔  No change for 3 TABs – assume end of form.")
                        break
                pass # End of loop, resets no_change_count if found
                if res: no_change_count = 0

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted. Saving...")
        
        # Atomic Write (Network Safe)
        tmp_file = self.output_file + ".tmp"
        with open(tmp_file, 'w') as f:
            json.dump(self.map_data, f, indent=4)
        try:
            os.replace(tmp_file, self.output_file)
            print(f"\n✅ Saved {len(self.map_data['fields'])} fields to {self.output_file}")
        except OSError:
            fallback = f"{self.output_file}.{int(time.time())}.json"
            os.replace(tmp_file, fallback)
            print(f"\n⚠️  SMB Error. Map saved to {fallback} – please copy manually.")

    def _resolution_match(self, saved, current, tol=0.05):
        """Fuzzy Resolution Match (5% tolerance)."""
        sw, sh = saved
        cw, ch = current
        dw = abs(sw - cw) / sw
        dh = abs(sh - ch) / sh
        return dw < tol and dh < tol

    def _clamp_click(self, x, y):
        """[FIX] Clamp clicks to screen bounds."""
        w, h = pyautogui.size()
        return int(max(0, min(x, w-1))), int(max(0, min(y, h-1)))

    def run_automation(self, input_data, dry_run=False, screencap=False):
        # [FIX] Re-arm FailSafe
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

        if not os.path.exists(self.output_file):
            print("No map."); return

        with open(self.output_file, 'r') as f:
            data = json.load(f)

        # 1. Fuzzy Resolution Check
        if not self._resolution_match(data["meta"]["resolution"], pyautogui.size()):
            print(f"WARNING: Res Change! Map:{data['meta']['resolution']} Cur:{pyautogui.size()}")
            if input("Continue? [y/N] ").lower() != 'y': return

        # 3. DPI Normalization (Ratio Multiplier)
        # [FIX] If saved=1.0 and current=1.5, we must MULTIPLY by 1.5/1.0 = 1.5 to scale up
        saved_scale = data["meta"].get("dpi_scale", 1.0)
        current_scale = self.dpi_scale
        scale_ratio = current_scale / saved_scale
        
        # Scrub Secrets for Log
        safe_data = copy.deepcopy(input_data)
        for k, v in safe_data.items():
            if isinstance(v, str) and len(v) > 3:
                safe_data[k] = '*' * len(v)
        print(f"\n=== RUNNING (Dry-Run={dry_run}, ScreenCap={screencap}) ===")
        print(f"Input: {safe_data}")
        
        self.ensure_focus()

        # [FIX] DPI Race Condition: Re-query DPI after focus
        try:
            rdp = gw.getWindowsWithTitle('Remote Desktop')[0]
            current_scale = ctypes.windll.user32.GetDpiForWindow(rdp._hWnd) / 96.0
        except:
            current_scale = self.dpi_scale
        scale_ratio = current_scale / saved_scale

        for fld in data["fields"]:
            name = fld["name"]
            ftype = fld["type"]
            x, y, w, h = fld["coords"]
            
            # [FIX] Apply DPI Scaling (Dynamic)
            cx = (x + w//2) * scale_ratio
            cy = (y + h//2) * scale_ratio

            # [FIX] Clamp
            cx, cy = self._clamp_click(cx, cy)
            
            if name not in input_data: continue
            
            print(f"Action: {name} ({ftype}) at {cx},{cy}")
            
            try:
                if dry_run:
                    print(f"  [DRY] Click {cx},{cy} -> Type")
                else:
                    if ftype == 'double_click':
                        pyautogui.doubleClick(cx, cy)
                    else:
                        pyautogui.click(cx, cy)

                    time.sleep(0.2)
                    
                    val = input_data[name]
                    if ftype == 'text':
                        pyautogui.hotkey('ctrl', 'a')
                        pyautogui.press('backspace')
                        # Use clipboard paste for unicode support
                        val_str = str(val)
                        pyperclip.copy(val_str)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.1)
                    elif ftype == 'toggle' and val:
                        pyautogui.press('space')
                    elif ftype == 'click':
                        pass
                    elif ftype == 'double_click':
                        pass
                    elif ftype == 'dropdown':
                        # Dropdown: click, wait, then select by typing or arrow keys
                        time.sleep(0.3)  # Wait for dropdown to open
                        val_str = str(val)
                        if val_str.startswith('arrow:'):
                            # Format: "arrow:3" = press down 3 times
                            try:
                                count = int(val_str.split(':')[1])
                                # Robust Navigation: Home + Down
                                pyautogui.press('home')
                                time.sleep(0.1)
                                
                                count = min(count, 50) # Safety cap
                                for _ in range(count):
                                    pyautogui.press('down')
                                    time.sleep(0.05)
                                pyautogui.press('enter')
                            except Exception as e:
                                print(f"  ❌ Invalid arrow format: {val_str} ({e})")
                        else:
                            # Type to filter/search
                            pyautogui.write(val_str)
                            time.sleep(0.2)
                            pyautogui.press('enter')
                        
                    # [FEATURE] Step Screenshot
                    if screencap:
                        time.sleep(0.5) # Wait for UI to react
                        sname = f"step_{name}_{int(time.time())}.png"
                        pyautogui.screenshot(sname)
                        print(f"  > Saved step shot: {sname}")

            except Exception as e:
                sname = f"error_{name}_{int(time.time())}.png"
                pyautogui.screenshot(sname)
                print(f"ERROR on {name}: {e}. Saved {sname}")
                if not dry_run: raise

def print_help():
    """Print beginner-friendly help."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   VISUAL SONAR - WVD Automation              ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
  python visual_sonar.py <command>

COMMANDS:
  map     Start mapping mode. The bot will press TAB and detect
          fields visually. You name each field as it's detected.
          
  run     Execute automation using wvd_map.json and input.json.
          Make sure to edit input.json with your data first!
          
  help    Show this help message.

QUICK START:
  1. Open your WVD/Citrix window
  2. Run: python visual_sonar.py map
  3. Edit input.json with your values
  4. Run: python visual_sonar.py run

FIELD TYPES (use during mapping):
  username:text        → Click, clear, and type the value
  submit:click         → Just click the field
  remember_me:toggle   → Click and press Space (for checkboxes)
  country:dropdown     → Click, type to filter OR use "arrow:N"
  app_icon:double_click → Double-click (for desktop icons)

DROPDOWN INPUT VALUES:
  "India"    → Types "India" to filter, then Enter
  "arrow:3"  → Press Down 3 times, then Enter

SAFETY:
  Move mouse to TOP-LEFT corner to emergency stop!
""")


def _run_cli(bot):
    """Internal CLI runner."""
    if len(sys.argv) < 2:
        print("\n┌─────────────────────────────────────┐")
        print("│   Welcome to Visual Sonar!          │")
        print("└─────────────────────────────────────┘")
        print("  Tip: Run 'visual-sonar help' for full guide.\n")
        mode = input("Select mode (map/run/help): ").strip().lower()
    else:
        mode = sys.argv[1].lower()

    if mode == 'help':
        print_help()
    elif mode == 'list':
        # List available test cases
        print("\n┌─────────────────────────────────────┐")
        print("│   AVAILABLE TEST CASES              │")
        print("└─────────────────────────────────────┘")
        
        # Check for test_cases directory
        tc_dir = "test_cases"
        if os.path.exists(tc_dir):
            cases = [f for f in os.listdir(tc_dir) if f.endswith('.json')]
            if cases:
                for i, case in enumerate(sorted(cases), 1):
                    print(f"  {i}. {case}")
                print(f"\n  Usage: python visual_sonar.py run test_cases/{cases[0]}")
            else:
                print("  No test cases found in test_cases/")
        else:
            print("  📁 No test_cases/ directory found.")
            print("\n  Create test cases like this:")
            print("     mkdir test_cases")
            print('     echo {"username": "user1"} > test_cases/login_test.json')
        
        # Also check input.json
        if os.path.exists("input.json"):
            print("\n  Default: input.json (exists)")
        print("\n  💡 Tip: Run with custom input file:")
        print("     python visual_sonar.py run <input_file.json>")
        print("\n  💡 Data-driven testing (multiple runs):")
        print("     python visual_sonar.py batch <data_file.csv>")
        
    elif mode == 'batch':
        # Data-driven testing - run same test with multiple data sets
        if len(sys.argv) < 3:
            print("\n❌ ERROR: No data file specified!")
            print("\n   Usage: python visual_sonar.py batch <data_file>")
            print("\n   Supported formats:")
            print("     • CSV:  data.csv (first row = headers as field names)")
            print("     • JSON: data.json (array of objects)")
            print("\n   Example CSV:")
            print("     username,password,signin")
            print("     user1@co.com,pass1,true")
            print("     user2@co.com,pass2,true")
            print("\n   Example JSON:")
            print('     [{"username": "user1", "password": "pass1", "signin": true},')
            print('      {"username": "user2", "password": "pass2", "signin": true}]')
            sys.exit(1)
        
        data_file = sys.argv[2]
        if not os.path.exists(data_file):
            print(f"\n❌ ERROR: Data file not found: {data_file}")
            sys.exit(1)
        
        # Load map file
        if not os.path.exists(bot.output_file):
            print("\n❌ ERROR: No map file found!")
            print(f"   Expected: {bot.output_file}")
            print("\n   FIX: Run 'python visual_sonar.py map' first.")
            sys.exit(1)
        
        # Parse data file
        test_data_rows = []
        if data_file.endswith('.csv'):
            import csv
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string 'true'/'false' to bool
                    parsed_row = {}
                    for k, v in row.items():
                        if v.lower() == 'true':
                            parsed_row[k] = True
                        elif v.lower() == 'false':
                            parsed_row[k] = False
                        else:
                            parsed_row[k] = v
                    test_data_rows.append(parsed_row)
        elif data_file.endswith('.json'):
            with open(data_file, 'r') as f:
                test_data_rows = json.load(f)
                if not isinstance(test_data_rows, list):
                    print("❌ ERROR: JSON must be an array of objects!")
                    sys.exit(1)
        else:
            print(f"❌ ERROR: Unsupported file format. Use .csv or .json")
            sys.exit(1)
        
        print(f"\n┌─────────────────────────────────────┐")
        print(f"│   BATCH RUN - {len(test_data_rows)} TEST CASES         │")
        print(f"└─────────────────────────────────────┘")
        print(f"  Data file: {data_file}")
        print(f"  Map: {bot.output_file}")
        
        # Preview first few rows
        print("\n  Preview:")
        for i, row in enumerate(test_data_rows[:3], 1):
            # Scrub sensitive data for preview
            preview = {k: ('***' if k in ['password'] else v) for k, v in row.items()}
            print(f"    {i}. {preview}")
        if len(test_data_rows) > 3:
            print(f"    ... and {len(test_data_rows) - 3} more")
        
        print("\n" + "─" * 40)
        print("  ⚠️  SAFETY: Move mouse to TOP-LEFT to abort!")
        print("─" * 40)
        
        confirm = input("\nProceed with all test cases? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)
        
        # Run each test case
        results = {"passed": 0, "failed": 0, "errors": []}
        for i, data in enumerate(test_data_rows, 1):
            print(f"\n{'='*50}")
            print(f"  TEST CASE {i}/{len(test_data_rows)}")
            print(f"{'='*50}")
            
            try:
                bot.run_automation(data, dry_run=False, screencap=True)
                results["passed"] += 1
                print(f"  ✅ Test case {i} PASSED")
            except KeyboardInterrupt:
                print("\n⛔ Batch run aborted by user.")
                break
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"case": i, "error": str(e)})
                print(f"  ❌ Test case {i} FAILED: {e}")
            
            # Pause between runs (allow UI to settle)
            if i < len(test_data_rows):
                print("  ⏳ Waiting 2s before next test...")
                time.sleep(2)
        
        # Summary
        print(f"\n{'='*50}")
        print(f"  BATCH RUN SUMMARY")
        print(f"{'='*50}")
        print(f"  ✅ Passed: {results['passed']}")
        print(f"  ❌ Failed: {results['failed']}")
        if results["errors"]:
            print("\n  Errors:")
            for err in results["errors"]:
                print(f"    Case {err['case']}: {err['error']}")
        
    elif mode == 'map':
        print("\n🎯 MAPPING MODE")
        print("─" * 40)
        print("• Keep your mouse AWAY from the WVD window")
        print("• The bot will press TAB automatically")
        print("• Name each field as: name:type")
        print("• Valid types: text, click, toggle, double_click")
        print("• Type 'skip' to ignore a field")
        print("• Type 'exit' to finish and save")
        print("─" * 40)
        input("\nPress Enter when ready...")
        bot.map_form()
    elif mode == 'run':
        # Load map file
        if not os.path.exists(bot.output_file):
            print("\n❌ ERROR: No map file found!")
            print(f"   Expected: {bot.output_file}")
            print("\n   FIX: Run 'python visual_sonar.py map' first to create it.")
            sys.exit(1)
        
        with open(bot.output_file, 'r') as f:
            map_data = json.load(f)
        
        # Load input file - allow custom file as argument
        if len(sys.argv) >= 3:
            input_file = sys.argv[2]
        else:
            input_file = "input.json"
            
        if not os.path.exists(input_file):
            print(f"\n❌ ERROR: No input file found!")
            print(f"   Expected: {input_file}")
            print("\n   FIX: Create the input file with your data. Example:")
            print('   {"username": "myuser", "password": "mypass"}')
            print("\n   💡 Or specify a different file:")
            print("      python visual_sonar.py run my_test.json")
            print("\n   💡 List available test cases:")
            print("      python visual_sonar.py list")
            sys.exit(1)
        
        with open(input_file, 'r') as f:
            d = json.load(f)
        
        # Validate input keys match map fields
        map_fields = {f["name"] for f in map_data["fields"]}
        input_keys = set(d.keys())
        
        missing = map_fields - input_keys
        extra = input_keys - map_fields
        
        print("\n┌─────────────────────────────────────┐")
        print("│   PRE-RUN CHECKLIST                 │")
        print("└─────────────────────────────────────┘")
        print(f"  Map: {bot.output_file} ({len(map_fields)} fields)")
        print(f"  Input: {input_file} ({len(input_keys)} values)")
        
        if missing:
            print(f"\n  ⚠️  Missing inputs for: {', '.join(missing)}")
            print("     (These fields will be SKIPPED)")
        if extra:
            print(f"\n  ℹ️  Extra keys ignored: {', '.join(extra)}")
        
        print("\n  Fields to execute:")
        for f in map_data["fields"]:
            status = "✓" if f["name"] in input_keys else "✗ (skip)"
            print(f"    {status} {f['name']} ({f['type']})")
        
        print("\n" + "─" * 40)
        print("  ⚠️  SAFETY: Move mouse to TOP-LEFT to abort!")
        print("─" * 40)
        
        confirm = input("\nProceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)
        
        try:
            bot.run_automation(d, dry_run=False, screencap=True)
            print("\n✅ Automation completed successfully!")
        except KeyboardInterrupt:
            print("\n⛔ Aborted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    elif mode == 'extract':
        # OCR Text Extraction Mode
        print("\n┌─────────────────────────────────────┐")
        print("│   OCR TEXT EXTRACTION               │")
        print("└─────────────────────────────────────┘")
        
        if OCR_BACKEND is None:
            print("\n❌ ERROR: No OCR backend installed!")
            print("   Option 1: pip install easyocr (pure Python, ~150MB models)")
            print("   Option 2: pip install pytesseract (requires Tesseract-OCR software)")
            print("\n   For pytesseract, also install Tesseract-OCR from:")
            print("   https://github.com/UB-Mannheim/tesseract/wiki")
            sys.exit(1)
        
        print(f"  Using OCR backend: {OCR_BACKEND}")
        
        # Check for subcommand
        if len(sys.argv) < 3:
            print("\n   Usage:")
            print("     python visual_sonar.py extract screen")
            print("     python visual_sonar.py extract region <x> <y> <width> <height>")
            print("     python visual_sonar.py extract field <field_name>")
            print("     python visual_sonar.py extract verify <x> <y> <w> <h> <expected_text>")
            print("\n   Examples:")
            print("     python visual_sonar.py extract screen")
            print("     python visual_sonar.py extract region 100 200 300 50")
            print("     python visual_sonar.py extract field username")
            print('     python visual_sonar.py extract verify 100 200 300 50 "Success"')
            sys.exit(1)
        
        subcommand = sys.argv[2].lower()
        
        if subcommand == 'screen':
            print("  📸 Capturing full screen...")
            text, results = bot.extract_text_from_screen()
            print(f"\n  Extracted Text ({len(results)} items):")
            print("  " + "─" * 40)
            for bbox, txt, conf in results:
                print(f"    [{conf:.2f}] {txt}")
            print("  " + "─" * 40)
            print(f"\n  Combined: {text[:500]}{'...' if len(text) > 500 else ''}")
            
            # Save to file
            out_file = f"ocr_output_{int(time.time())}.txt"
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"\n  💾 Saved to: {out_file}")
            
        elif subcommand == 'region':
            if len(sys.argv) < 7:
                print("❌ ERROR: Need coordinates: extract region <x> <y> <width> <height>")
                sys.exit(1)
            x, y, w, h = map(int, sys.argv[3:7])
            print(f"  📸 Capturing region ({x}, {y}, {w}x{h})...")
            text, results = bot.extract_text_from_region(x, y, w, h)
            print(f"\n  Extracted Text ({len(results)} items):")
            print("  " + "─" * 40)
            for bbox, txt, conf in results:
                print(f"    [{conf:.2f}] {txt}")
            print("  " + "─" * 40)
            print(f"\n  Combined: {text}")
            
        elif subcommand == 'field':
            if len(sys.argv) < 4:
                print("❌ ERROR: Need field name: extract field <field_name>")
                sys.exit(1)
            field_name = sys.argv[3]
            print(f"  📸 Extracting text from mapped field '{field_name}'...")
            try:
                text, results = bot.extract_text_from_field(field_name)
                print(f"\n  Extracted: {text}")
            except Exception as e:
                print(f"❌ ERROR: {e}")
                sys.exit(1)
                
        elif subcommand == 'verify':
            if len(sys.argv) < 8:
                print('❌ ERROR: Need coordinates and text: extract verify <x> <y> <w> <h> "expected text"')
                sys.exit(1)
            x, y, w, h = map(int, sys.argv[3:7])
            expected = sys.argv[7]
            print(f"  🔍 Verifying region ({x}, {y}, {w}x{h}) contains: '{expected}'...")
            
            if bot.verify_text_contains([x, y, w, h], expected):
                print(f"  ✅ PASS: Text '{expected}' found!")
            else:
                print(f"  ❌ FAIL: Text '{expected}' NOT found!")
                sys.exit(1)
        else:
            print(f"❌ Unknown extract subcommand: {subcommand}")
            
    else:
        print(f"\n❌ Unknown command: '{mode}'")
        print("   Valid commands: map, run, list, batch, extract, help")
        print("   Run 'visual-sonar help' for more info.")


def main():
    """Main entry point for the visual-sonar CLI command."""
    # Handle help first
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['help', '--help', '-h']:
        print_help()
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['--version', '-v']:
        print(f"Visual Sonar v{__version__}")
        sys.exit(0)
    
    bot = VisualSonar()
    _run_cli(bot)


if __name__ == "__main__":
    main()
