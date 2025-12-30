"""
Session switcher component
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import asyncio
import threading
from typing import Dict, Callable, Optional

from core.client import TelegramClientWrapper
from utils.constants import BOLD_FONT


class SessionSwitcher:
    """Component for switching between Telegram sessions"""

    def __init__(
            self,
            parent: tk.Widget,
            shared_vars: dict,
            log_callback: Callable[[str], None],
            on_session_changed: Optional[Callable[[str], None]] = None
    ):
        self.parent = parent
        self.shared_vars = shared_vars
        self.log = log_callback
        self.on_session_changed = on_session_changed
        self.session_accounts: Dict[str, str] = {}

        self.frame = self._create_widget()

    def _create_widget(self) -> ttk.LabelFrame:
        """Create the session switcher widget"""
        frame = ttk.LabelFrame(self.parent, text="🔄 Session Switcher", padding="10")

        # Session dropdown
        ttk.Label(frame, text="Select Session:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.session_dropdown = ttk.Combobox(
            frame,
            textvariable=self.shared_vars['session_name'],
            width=40
        )
        self.session_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.session_dropdown.bind('<<ComboboxSelected>>', self._on_session_selected)

        ttk.Button(
            frame,
            text="🔄 Refresh",
            command=self.refresh_sessions
        ).grid(row=0, column=2, padx=5)

        # Session info display
        ttk.Label(
            frame,
            textvariable=self.shared_vars['session_info'],
            font=BOLD_FONT,
            foreground="green"
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # New session entry
        ttk.Label(frame, text="Or create new:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )

        ttk.Entry(
            frame,
            textvariable=self.shared_vars['new_session'],
            width=30
        ).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(
            frame,
            text="➕ Create & Login",
            command=self._create_new_session
        ).grid(row=2, column=2, padx=5)

        return frame

    def _on_session_selected(self, event) -> None:
        """Handle session selection from dropdown"""
        selected = self.session_dropdown.get()

        # Extract session name (remove account info if present)
        if ' (' in selected:
            session_name = selected.split(' (')[0]
        else:
            session_name = selected

        self.shared_vars['session_name'].set(session_name)

        # Update session info display
        if session_name in self.session_accounts:
            self.shared_vars['session_info'].set(
                f"👤 {self.session_accounts[session_name]}"
            )
        else:
            self.shared_vars['session_info'].set("")

        self.log(f"🔄 Switched to session: {session_name}")

        if self.on_session_changed:
            self.on_session_changed(session_name)

    def _create_new_session(self) -> None:
        """Create a new session and open login dialog"""
        new_name = self.shared_vars['new_session'].get().strip()

        if not new_name:
            messagebox.showwarning("Warning", "Please enter a session name")
            return

        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']
        if any(c in new_name for c in invalid_chars):
            messagebox.showerror(
                "Error",
                "Session name cannot contain special characters or spaces"
            )
            return

        # Check if session already exists
        if os.path.exists(f"{new_name}.session"):
            if not messagebox.askyesno(
                    "Session Exists",
                    f"Session '{new_name}' already exists. Switch to it?"
            ):
                return
            self.shared_vars['session_name'].set(new_name)
            self._on_session_selected(None)
            return

        # Set the new session name
        self.shared_vars['session_name'].set(new_name)
        self.shared_vars['new_session'].set("")
        self.log(f"📝 Created new session: {new_name}")

        # Open login dialog
        api_id = self.shared_vars['api_id'].get()
        api_hash = self.shared_vars['api_hash'].get()

        if not api_id or not api_hash:
            messagebox.showwarning(
                "Warning",
                "Please enter API ID and API Hash in Settings first"
            )
            return

        from ui.components.login_dialog import show_login_dialog

        def on_login_success(user_name: str):
            self.log(f"✅ Logged in as {user_name}")
            self.shared_vars['session_info'].set(f"👤 {user_name}")
            self.session_accounts[new_name] = user_name
            self.refresh_sessions()

            if self.on_session_changed:
                self.on_session_changed(new_name)

        def on_login_failure(error: str):
            self.log(f"❌ Login failed: {error}")

        show_login_dialog(
            parent=self.parent.winfo_toplevel(),
            api_id=int(api_id),
            api_hash=api_hash,
            session_name=new_name,
            on_success=on_login_success,
            on_failure=on_login_failure
        )

    def refresh_sessions(self) -> None:
        """Refresh the session dropdown list"""
        sessions = TelegramClientWrapper.detect_sessions()
        current_session = self.shared_vars['session_name'].get()

        if sessions:
            self.session_dropdown['values'] = sessions
            self.log(f"🔍 Found {len(sessions)} session(s): {', '.join(sessions)}")
        else:
            self.session_dropdown['values'] = [current_session]
            self.log("ℹ️ No existing sessions found.")

        # Check account info
        self._check_all_sessions_info(sessions)

    def _check_all_sessions_info(self, sessions) -> None:
        """Check account info for all sessions"""
        api_id = self.shared_vars['api_id'].get()
        api_hash = self.shared_vars['api_hash'].get()

        if not api_id or not api_hash:
            return

        def run_check():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                api_id_int = int(api_id)

                async def check_all():
                    results = {}
                    for session in sessions:
                        info = await TelegramClientWrapper.get_session_info(
                            api_id_int, api_hash, session
                        )
                        results[info['name']] = info['info']
                    return results

                results = loop.run_until_complete(check_all())
                self.session_accounts = results

                # Update UI on main thread
                root = self.parent.winfo_toplevel()
                root.after(0, self._update_session_display)

            except Exception:
                pass
            finally:
                loop.close()

        threading.Thread(target=run_check, daemon=True).start()

    def _update_session_display(self) -> None:
        """Update the session dropdown with account info"""
        sessions = TelegramClientWrapper.detect_sessions()
        display_values = []

        for session in sessions:
            if session in self.session_accounts:
                display_values.append(
                    f"{session} ({self.session_accounts[session]})"
                )
            else:
                display_values.append(session)

        if display_values:
            self.session_dropdown['values'] = display_values

        # Update current session info
        current_session = self.shared_vars['session_name'].get()
        if current_session in self.session_accounts:
            self.shared_vars['session_info'].set(
                f"👤 {self.session_accounts[current_session]}"
            )