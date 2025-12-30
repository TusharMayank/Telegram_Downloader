"""
Settings tab UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import asyncio

from core.client import TelegramClientWrapper
from ui.components.session_switcher import SessionSwitcher


class SettingsTab:
    """Settings tab"""

    def __init__(self, parent, shared_vars, logger, app, config_manager):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app
        self.config_manager = config_manager

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Session Switcher
        self.session_switcher = SessionSwitcher(
            self.frame,
            self.shared_vars,
            self.logger.log,
            on_session_changed=self._on_session_changed
        )
        self.session_switcher.frame.pack(fill=tk.X, pady=(0, 10))

        # API Credentials
        api_frame = ttk.LabelFrame(
            self.frame,
            text="Telegram API Credentials",
            padding="10"
        )
        api_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(api_frame, text="API ID:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Entry(
            api_frame,
            textvariable=self.shared_vars['api_id'],
            width=30
        ).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(api_frame, text="API Hash:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.api_hash_entry = ttk.Entry(
            api_frame,
            textvariable=self.shared_vars['api_hash'],
            width=40,
            show="*"
        )
        self.api_hash_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Checkbutton(
            api_frame,
            text="Show",
            variable=self.shared_vars['show_hash'],
            command=self._toggle_hash_visibility
        ).grid(row=1, column=2, padx=5)

        ttk.Label(
            api_frame,
            text="Get credentials from: https://my.telegram.org/apps",
            foreground="blue"
        ).grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Channel Configuration
        channel_frame = ttk.LabelFrame(
            self.frame,
            text="Channel Configuration",
            padding="10"
        )
        channel_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(channel_frame, text="Channel ID:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Entry(
            channel_frame,
            textvariable=self.shared_vars['channel_id'],
            width=30
        ).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(
            channel_frame,
            text="(From URL: t.me/c/CHANNEL_ID/post)"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)

        # Connection & Login
        test_frame = ttk.LabelFrame(
            self.frame,
            text="Connection & Login",
            padding="10"
        )
        test_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            test_frame,
            text="🔌 Test Connection",
            command=self._test_connection
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            test_frame,
            text="🔑 Login",
            command=self._login
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            test_frame,
            text="🚪 Logout",
            command=self._logout
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            test_frame,
            text="🗑️ Delete Session",
            command=self._delete_session
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            test_frame,
            textvariable=self.shared_vars['connection_status']
        ).pack(side=tk.LEFT, padx=20)

        # Save Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="💾 Save Settings",
            command=self._save_settings
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🔄 Reset",
            command=self._reset_settings
        ).pack(side=tk.LEFT, padx=5)

        # Help
        help_frame = ttk.LabelFrame(self.frame, text="Help", padding="10")
        help_frame.pack(fill=tk.BOTH, expand=True)

        help_text = """
How to use:

1. Get API credentials from https://my.telegram.org/apps

2. Enter API ID and API Hash, then Save

3. Select or create a session, then Login

4. Go to Download tab to download audio files

5. Channel ID is from URL: t.me/c/CHANNEL_ID/post
        """

        ttk.Label(help_frame, text=help_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _toggle_hash_visibility(self) -> None:
        """Toggle API hash visibility"""
        show = "" if self.shared_vars['show_hash'].get() else "*"
        self.api_hash_entry.config(show=show)

    def _on_session_changed(self, session_name: str) -> None:
        """Handle session change"""
        self._test_connection()

    def refresh_sessions(self) -> None:
        """Refresh sessions list"""
        self.session_switcher.refresh_sessions()

    def _test_connection(self) -> None:
        """Test connection"""
        if not self.app.validate_settings():
            return

        self.shared_vars['connection_status'].set("Testing...")

        def run_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def test():
                    info = await TelegramClientWrapper.get_session_info(
                        int(self.shared_vars['api_id'].get()),
                        self.shared_vars['api_hash'].get(),
                        self.shared_vars['session_name'].get()
                    )
                    return info

                info = loop.run_until_complete(test())

                if info['authorized']:
                    result = f"✅ Connected as {info['info']}"
                    self.frame.after(
                        0,
                        lambda: self.shared_vars['active_session'].set(
                            f"Session: {info['name']} - 👤 {info['info']}"
                        )
                    )
                else:
                    result = "⚠️ Not logged in"

                self.frame.after(
                    0,
                    lambda: self.shared_vars['connection_status'].set(result)
                )
                self.frame.after(0, lambda: self.logger.log(result))

            except Exception as e:
                self.frame.after(
                    0,
                    lambda: self.shared_vars['connection_status'].set(f"❌ Error")
                )
                self.frame.after(0, lambda: self.logger.log(f"❌ Error: {str(e)}"))
            finally:
                loop.close()

        threading.Thread(target=run_test, daemon=True).start()

    def _login(self) -> None:
        """Login to Telegram using GUI dialog"""
        if not self.app.validate_settings():
            return

        from ui.components.login_dialog import show_login_dialog

        session_name = self.shared_vars['session_name'].get()

        def on_login_success(user_name: str):
            """Handle successful login"""
            self.logger.log(f"✅ Logged in as {user_name}")
            self.shared_vars['connection_status'].set(f"✅ Logged in as {user_name}")
            self.shared_vars['session_info'].set(f"👤 {user_name}")
            self.shared_vars['active_session'].set(
                f"Session: {session_name} - 👤 {user_name}"
            )
            self.refresh_sessions()

        def on_login_failure(error: str):
            """Handle login failure"""
            self.logger.log(f"❌ Login failed: {error}")

        # Show login dialog
        show_login_dialog(
            parent=self.frame.winfo_toplevel(),
            api_id=int(self.shared_vars['api_id'].get()),
            api_hash=self.shared_vars['api_hash'].get(),
            session_name=session_name,
            on_success=on_login_success,
            on_failure=on_login_failure
        )

        def run_login():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def login():
                    client = TelegramClientWrapper(
                        int(self.shared_vars['api_id'].get()),
                        self.shared_vars['api_hash'].get(),
                        session_name
                    )
                    await client.connect()
                    await client.start()
                    me = await client.get_me()
                    await client.disconnect()
                    return me.first_name

                name = loop.run_until_complete(login())
                result = f"✅ Logged in as {name}"

                self.frame.after(
                    0,
                    lambda: self.shared_vars['connection_status'].set(result)
                )
                self.frame.after(0, lambda: self.logger.log(result))
                self.frame.after(0, self.refresh_sessions)

            except Exception as e:
                self.frame.after(0, lambda: self.logger.log(f"❌ Error: {str(e)}"))
            finally:
                loop.close()

        threading.Thread(target=run_login, daemon=True).start()

    def _logout(self) -> None:
        """Logout from current session"""
        session_name = self.shared_vars['session_name'].get()
        session_file = f"{session_name}.session"

        if os.path.exists(session_file):
            if messagebox.askyesno("Confirm", f"Logout from '{session_name}'?"):
                try:
                    os.remove(session_file)
                    self.logger.log(f"✅ Logged out: {session_name}")
                    self.shared_vars['connection_status'].set("Logged out")
                    self.shared_vars['session_info'].set("")
                    self.shared_vars['active_session'].set("No session active")
                    self.refresh_sessions()
                except Exception as e:
                    self.logger.log(f"❌ Error: {str(e)}")
        else:
            self.logger.log("No active session found")

    def _delete_session(self) -> None:
        """Delete session file"""
        session_name = self.shared_vars['session_name'].get()
        session_file = f"{session_name}.session"

        if not os.path.exists(session_file):
            messagebox.showinfo("Info", "Session file does not exist")
            return

        if messagebox.askyesno(
                "Confirm Delete",
                f"Delete session '{session_name}'?"
        ):
            try:
                os.remove(session_file)
                self.logger.log(f"🗑️ Deleted: {session_name}")
                self.shared_vars['connection_status'].set("Deleted")
                self.shared_vars['session_info'].set("")
                self.refresh_sessions()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _save_settings(self) -> None:
        """Save settings"""
        config_data = {
            'api_id': self.shared_vars['api_id'].get(),
            'api_hash': self.shared_vars['api_hash'].get(),
            'channel_id': self.shared_vars['channel_id'].get(),
            'output_dir': self.shared_vars['output_dir'].get(),
            'session_name': self.shared_vars['session_name'].get()
        }

        if self.config_manager.save(config_data):
            self.logger.log("✅ Settings saved!")
        else:
            self.logger.log("❌ Failed to save settings")

    def _reset_settings(self) -> None:
        """Reset to defaults"""
        defaults = self.config_manager.reset()

        self.shared_vars['api_id'].set(defaults['api_id'])
        self.shared_vars['api_hash'].set(defaults['api_hash'])
        self.shared_vars['channel_id'].set(defaults['channel_id'])
        self.shared_vars['output_dir'].set(defaults['output_dir'])
        self.shared_vars['session_name'].set(defaults['session_name'])

        self.logger.log("🔄 Settings reset to defaults")