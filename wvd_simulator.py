"""
WVD Simulator - Test Visual Sonar without a real Remote Desktop

This creates a fake "WVD Login" window that:
- Shows clear focus rings when TAB is pressed
- Accepts input and logs what was typed
- Lets you test mapping → execution flow safely

Usage:
    python wvd_simulator.py

Then in another terminal:
    python visual_sonar.py map
"""

import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime

class WVDSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Remote Desktop - Simulator")
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a2e")
        
        # Log for tracking inputs
        self.action_log = []
        
        self._create_ui()
        self._setup_logging()
        
    def _create_ui(self):
        """Create a WVD-like login form."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title = tk.Label(
            main_frame, 
            text="🖥️ WVD Login Simulator",
            font=("Segoe UI", 24, "bold"),
            fg="#00d4ff",
            bg="#1a1a2e"
        )
        title.pack(pady=(0, 30))
        
        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="Use this window to test Visual Sonar mapping & automation",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1a1a2e"
        )
        subtitle.pack(pady=(0, 20))
        
        # Form container with border
        form_frame = tk.Frame(main_frame, bg="#16213e", padx=40, pady=30)
        form_frame.pack()
        
        # Username field
        tk.Label(
            form_frame,
            text="Username",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#16213e",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.username_entry = tk.Entry(
            form_frame,
            font=("Segoe UI", 12),
            width=35,
            bg="#0f0f23",
            fg="#ffffff",
            insertbackground="#00d4ff",
            highlightthickness=3,
            highlightcolor="#00d4ff",  # Focus ring color
            highlightbackground="#333333",
            relief="flat"
        )
        self.username_entry.pack(pady=(0, 15), ipady=8)
        
        # Password field
        tk.Label(
            form_frame,
            text="Password",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#16213e",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=("Segoe UI", 12),
            width=35,
            show="●",
            bg="#0f0f23",
            fg="#ffffff",
            insertbackground="#00d4ff",
            highlightthickness=3,
            highlightcolor="#00d4ff",
            highlightbackground="#333333",
            relief="flat"
        )
        self.password_entry.pack(pady=(0, 15), ipady=8)
        
        # Domain dropdown
        tk.Label(
            form_frame,
            text="Domain",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#16213e",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.domain_var = tk.StringVar(value="Select Domain")
        self.domain_combo = ttk.Combobox(
            form_frame,
            textvariable=self.domain_var,
            values=["CORP", "DEV", "STAGING", "PRODUCTION", "LOCAL"],
            font=("Segoe UI", 12),
            width=33,
            state="readonly"
        )
        self.domain_combo.pack(pady=(0, 15), ipady=5)
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar()
        self.remember_check = tk.Checkbutton(
            form_frame,
            text="Remember me",
            variable=self.remember_var,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#16213e",
            selectcolor="#0f0f23",
            activebackground="#16213e",
            activeforeground="#ffffff",
            highlightthickness=2,
            highlightcolor="#00d4ff",
            highlightbackground="#16213e"
        )
        self.remember_check.pack(anchor="w", pady=(0, 20))
        
        # Submit button
        self.submit_btn = tk.Button(
            form_frame,
            text="Sign In",
            font=("Segoe UI", 12, "bold"),
            bg="#00d4ff",
            fg="#000000",
            activebackground="#00a8cc",
            activeforeground="#000000",
            width=20,
            relief="flat",
            cursor="hand2",
            highlightthickness=3,
            highlightcolor="#ffff00",
            highlightbackground="#333333",
            command=self._on_submit
        )
        self.submit_btn.pack(pady=(0, 10), ipady=8)
        
        # Cancel button
        self.cancel_btn = tk.Button(
            form_frame,
            text="Cancel",
            font=("Segoe UI", 11),
            bg="#333333",
            fg="#ffffff",
            activebackground="#444444",
            activeforeground="#ffffff",
            width=20,
            relief="flat",
            cursor="hand2",
            highlightthickness=3,
            highlightcolor="#ff6b6b",
            highlightbackground="#333333",
            command=self._on_cancel
        )
        self.cancel_btn.pack(ipady=5)
        
        # Log display at bottom
        log_frame = tk.Frame(self.root, bg="#0f0f23")
        log_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        tk.Label(
            log_frame,
            text="📋 Action Log:",
            font=("Consolas", 10, "bold"),
            fg="#00d4ff",
            bg="#0f0f23",
            anchor="w"
        ).pack(fill="x")
        
        self.log_text = tk.Text(
            log_frame,
            height=6,
            font=("Consolas", 9),
            bg="#0a0a15",
            fg="#00ff00",
            relief="flat",
            state="disabled"
        )
        self.log_text.pack(fill="x", pady=(5, 0))
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready - Press TAB to navigate between fields",
            font=("Segoe UI", 9),
            fg="#666666",
            bg="#1a1a2e",
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill="x", padx=10)
        
        # Apply ttk style for combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", 
                        fieldbackground="#0f0f23",
                        background="#333333",
                        foreground="#ffffff")
        
    def _setup_logging(self):
        """Bind events to log interactions."""
        # Track focus changes
        for widget in [self.username_entry, self.password_entry, 
                       self.domain_combo, self.remember_check,
                       self.submit_btn, self.cancel_btn]:
            widget.bind("<FocusIn>", self._on_focus_in)
            widget.bind("<FocusOut>", self._on_focus_out)
        
        # Track key presses in entries
        self.username_entry.bind("<KeyRelease>", lambda e: self._log_input("username", self.username_entry.get()))
        self.password_entry.bind("<KeyRelease>", lambda e: self._log_input("password", "***"))
        
        # Track dropdown selection
        self.domain_combo.bind("<<ComboboxSelected>>", lambda e: self._log_action(f"Selected domain: {self.domain_var.get()}"))
        
        # Track checkbox
        self.remember_check.bind("<Button-1>", lambda e: self._log_action(f"Remember me: {not self.remember_var.get()}"))
        
    def _log_action(self, message):
        """Add an action to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.action_log.append(log_entry)
        
        self.log_text.configure(state="normal")
        self.log_text.insert("end", log_entry + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        
    def _log_input(self, field, value):
        """Log input to a field."""
        self._log_action(f"Input to {field}: {value}")
        
    def _on_focus_in(self, event):
        """Log when a widget gets focus."""
        widget_name = self._get_widget_name(event.widget)
        self._log_action(f"Focus → {widget_name}")
        self.status_label.config(text=f"Focused: {widget_name}")
        
    def _on_focus_out(self, event):
        """Log when a widget loses focus."""
        pass  # Focus in already logs the new focus
        
    def _get_widget_name(self, widget):
        """Get a friendly name for a widget."""
        if widget == self.username_entry:
            return "Username Field"
        elif widget == self.password_entry:
            return "Password Field"
        elif widget == self.domain_combo:
            return "Domain Dropdown"
        elif widget == self.remember_check:
            return "Remember Me Checkbox"
        elif widget == self.submit_btn:
            return "Sign In Button"
        elif widget == self.cancel_btn:
            return "Cancel Button"
        return "Unknown"
        
    def _on_submit(self):
        """Handle sign in click."""
        username = self.username_entry.get()
        domain = self.domain_var.get()
        remember = self.remember_var.get()
        
        self._log_action("=" * 40)
        self._log_action("🎉 SIGN IN CLICKED!")
        self._log_action(f"   Username: {username}")
        self._log_action(f"   Domain: {domain}")
        self._log_action(f"   Remember: {remember}")
        self._log_action("=" * 40)
        
        # Flash success
        self.submit_btn.config(bg="#00ff00", text="✓ Success!")
        self.root.after(2000, lambda: self.submit_btn.config(bg="#00d4ff", text="Sign In"))
        
    def _on_cancel(self):
        """Handle cancel click."""
        self._log_action("❌ Cancel clicked - clearing form")
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.domain_var.set("Select Domain")
        self.remember_var.set(False)
        
    def run(self):
        """Start the simulator."""
        self._log_action("Simulator started - ready for Visual Sonar testing!")
        self._log_action("Tip: Use 'python visual_sonar.py map' in another terminal")
        self.root.mainloop()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║              WVD SIMULATOR - For Testing Visual Sonar        ║
╠══════════════════════════════════════════════════════════════╣
║  This window simulates a WVD login form.                     ║
║                                                              ║
║  To test Visual Sonar:                                       ║
║    1. Keep this window visible                               ║
║    2. In another terminal: python visual_sonar.py map        ║
║    3. Map the fields: username:text, password:text, etc.     ║
║    4. Create input.json with test values                     ║
║    5. Run: python visual_sonar.py run                        ║
║                                                              ║
║  The log at the bottom shows all interactions!               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    simulator = WVDSimulator()
    simulator.run()
