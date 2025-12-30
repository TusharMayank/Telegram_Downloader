"""
Login dialog for Telegram authentication
Handles phone number and OTP input via GUI instead of console
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from typing import Optional, Callable

from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    FloodWaitError
)


class LoginDialog:
    """Dialog window for Telegram login"""

    def __init__(
            self,
            parent: tk.Tk,
            api_id: int,
            api_hash: str,
            session_name: str,
            on_success: Optional[Callable[[str], None]] = None,
            on_failure: Optional[Callable[[str], None]] = None
    ):
        self.parent = parent
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.on_success = on_success
        self.on_failure = on_failure

        self.client: Optional[TelegramClient] = None
        self.phone_code_hash: Optional[str] = None
        self.phone_number: Optional[str] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Telegram Login")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self._center_window()

        # Create UI
        self._create_widgets()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self) -> None:
        """Center the dialog on parent window"""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = 400
        dialog_height = 350

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create dialog widgets"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="🔐 Telegram Login",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Session info
        session_label = ttk.Label(
            main_frame,
            text=f"Session: {self.session_name}",
            font=('Arial', 10)
        )
        session_label.pack(pady=(0, 15))

        # Phone Number Frame
        self.phone_frame = ttk.LabelFrame(
            main_frame,
            text="Step 1: Enter Phone Number",
            padding="10"
        )
        self.phone_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            self.phone_frame,
            text="Phone (with country code):"
        ).pack(anchor=tk.W)

        phone_input_frame = ttk.Frame(self.phone_frame)
        phone_input_frame.pack(fill=tk.X, pady=5)

        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(
            phone_input_frame,
            textvariable=self.phone_var,
            width=25,
            font=('Arial', 12)
        )
        self.phone_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.phone_entry.bind('<Return>', lambda e: self._request_code())

        self.send_code_btn = ttk.Button(
            phone_input_frame,
            text="Send Code",
            command=self._request_code
        )
        self.send_code_btn.pack(side=tk.LEFT)

        ttk.Label(
            self.phone_frame,
            text="Example: +1234567890",
            foreground="gray"
        ).pack(anchor=tk.W)

        # OTP Frame
        self.otp_frame = ttk.LabelFrame(
            main_frame,
            text="Step 2: Enter Verification Code",
            padding="10"
        )
        self.otp_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            self.otp_frame,
            text="Verification Code:"
        ).pack(anchor=tk.W)

        otp_input_frame = ttk.Frame(self.otp_frame)
        otp_input_frame.pack(fill=tk.X, pady=5)

        self.otp_var = tk.StringVar()
        self.otp_entry = ttk.Entry(
            otp_input_frame,
            textvariable=self.otp_var,
            width=15,
            font=('Arial', 14),
            justify=tk.CENTER
        )
        self.otp_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.otp_entry.bind('<Return>', lambda e: self._verify_code())
        self.otp_entry.config(state=tk.DISABLED)

        self.verify_btn = ttk.Button(
            otp_input_frame,
            text="Verify & Login",
            command=self._verify_code,
            state=tk.DISABLED
        )
        self.verify_btn.pack(side=tk.LEFT)

        ttk.Label(
            self.otp_frame,
            text="Check your Telegram app for the code",
            foreground="gray"
        ).pack(anchor=tk.W)

        # 2FA Password Frame (hidden by default)
        self.password_frame = ttk.LabelFrame(
            main_frame,
            text="Step 3: Two-Factor Authentication",
            padding="10"
        )
        # Don't pack yet - will be shown if needed

        ttk.Label(
            self.password_frame,
            text="2FA Password:"
        ).pack(anchor=tk.W)

        password_input_frame = ttk.Frame(self.password_frame)
        password_input_frame.pack(fill=tk.X, pady=5)

        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            password_input_frame,
            textvariable=self.password_var,
            width=25,
            font=('Arial', 12),
            show="*"
        )
        self.password_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.password_entry.bind('<Return>', lambda e: self._verify_password())

        self.password_btn = ttk.Button(
            password_input_frame,
            text="Submit",
            command=self._verify_password
        )
        self.password_btn.pack(side=tk.LEFT)

        # Status
        self.status_var = tk.StringVar(value="Enter your phone number to begin")
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            wraplength=350
        )
        self.status_label.pack(pady=10)

        # Cancel button
        ttk.Button(
            main_frame,
            text="Cancel",
            command=self._on_close
        ).pack(pady=(10, 0))

        # Focus on phone entry
        self.phone_entry.focus_set()

    def _set_status(self, message: str, is_error: bool = False) -> None:
        """Update status message"""
        self.status_var.set(message)
        self.status_label.config(
            foreground="red" if is_error else "black"
        )
        self.dialog.update_idletasks()

    def _request_code(self) -> None:
        """Request verification code"""
        phone = self.phone_var.get().strip()

        if not phone:
            self._set_status("Please enter your phone number", True)
            return

        # Validate phone format
        if not phone.startswith('+'):
            phone = '+' + phone
            self.phone_var.set(phone)

        self.phone_number = phone
        self.send_code_btn.config(state=tk.DISABLED)
        self.phone_entry.config(state=tk.DISABLED)
        self._set_status("Sending verification code...")

        # Run in thread
        thread = threading.Thread(
            target=self._async_request_code,
            daemon=True
        )
        thread.start()

    def _async_request_code(self) -> None:
        """Async request code operation"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            result = self.loop.run_until_complete(
                self._send_code_request()
            )

            if result['success']:
                self.phone_code_hash = result['phone_code_hash']
                self.dialog.after(0, self._on_code_sent)
            else:
                self.dialog.after(
                    0,
                    lambda: self._on_code_error(result['error'])
                )

        except Exception as e:
            self.dialog.after(
                0,
                lambda: self._on_code_error(str(e))
            )

    async def _send_code_request(self) -> dict:
        """Send code request to Telegram"""
        try:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )

            await self.client.connect()

            # Check if already authorized
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                return {
                    'success': True,
                    'already_authorized': True,
                    'user': me.first_name
                }

            # Request code
            sent_code = await self.client.send_code_request(self.phone_number)

            return {
                'success': True,
                'already_authorized': False,
                'phone_code_hash': sent_code.phone_code_hash
            }

        except PhoneNumberInvalidError:
            return {
                'success': False,
                'error': 'Invalid phone number format'
            }
        except FloodWaitError as e:
            return {
                'success': False,
                'error': f'Too many attempts. Wait {e.seconds} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _on_code_sent(self) -> None:
        """Handle successful code send"""
        self._set_status("✅ Code sent! Check your Telegram app")
        self.otp_entry.config(state=tk.NORMAL)
        self.verify_btn.config(state=tk.NORMAL)
        self.otp_entry.focus_set()

    def _on_code_error(self, error: str) -> None:
        """Handle code send error"""
        self._set_status(f"❌ {error}", True)
        self.send_code_btn.config(state=tk.NORMAL)
        self.phone_entry.config(state=tk.NORMAL)

    def _verify_code(self) -> None:
        """Verify the entered code"""
        code = self.otp_var.get().strip()

        if not code:
            self._set_status("Please enter the verification code", True)
            return

        self.verify_btn.config(state=tk.DISABLED)
        self.otp_entry.config(state=tk.DISABLED)
        self._set_status("Verifying code...")

        # Run in thread
        thread = threading.Thread(
            target=self._async_verify_code,
            args=(code,),
            daemon=True
        )
        thread.start()

    def _async_verify_code(self, code: str) -> None:
        """Async verify code operation"""
        if not self.loop:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        try:
            result = self.loop.run_until_complete(
                self._sign_in_with_code(code)
            )

            if result['success']:
                self.dialog.after(
                    0,
                    lambda: self._on_login_success(result['user'])
                )
            elif result.get('needs_2fa'):
                self.dialog.after(0, self._show_2fa_input)
            else:
                self.dialog.after(
                    0,
                    lambda: self._on_verify_error(result['error'])
                )

        except Exception as e:
            self.dialog.after(
                0,
                lambda: self._on_verify_error(str(e))
            )

    async def _sign_in_with_code(self, code: str) -> dict:
        """Sign in with verification code"""
        try:
            if not self.client:
                return {'success': False, 'error': 'Client not connected'}

            # Sign in
            user = await self.client.sign_in(
                phone=self.phone_number,
                code=code,
                phone_code_hash=self.phone_code_hash
            )

            return {
                'success': True,
                'user': user.first_name
            }

        except PhoneCodeInvalidError:
            return {
                'success': False,
                'error': 'Invalid verification code'
            }
        except PhoneCodeExpiredError:
            return {
                'success': False,
                'error': 'Code expired. Please request a new one'
            }
        except SessionPasswordNeededError:
            return {
                'success': False,
                'needs_2fa': True,
                'error': '2FA required'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _on_verify_error(self, error: str) -> None:
        """Handle verification error"""
        self._set_status(f"❌ {error}", True)
        self.verify_btn.config(state=tk.NORMAL)
        self.otp_entry.config(state=tk.NORMAL)
        self.otp_var.set("")
        self.otp_entry.focus_set()

    def _show_2fa_input(self) -> None:
        """Show 2FA password input"""
        self._set_status("Two-Factor Authentication required")
        self.password_frame.pack(fill=tk.X, pady=(0, 10))
        self.password_entry.focus_set()

    def _verify_password(self) -> None:
        """Verify 2FA password"""
        password = self.password_var.get()

        if not password:
            self._set_status("Please enter your 2FA password", True)
            return

        self.password_btn.config(state=tk.DISABLED)
        self.password_entry.config(state=tk.DISABLED)
        self._set_status("Verifying password...")

        # Run in thread
        thread = threading.Thread(
            target=self._async_verify_password,
            args=(password,),
            daemon=True
        )
        thread.start()

    def _async_verify_password(self, password: str) -> None:
        """Async verify 2FA password"""
        if not self.loop:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        try:
            result = self.loop.run_until_complete(
                self._sign_in_with_password(password)
            )

            if result['success']:
                self.dialog.after(
                    0,
                    lambda: self._on_login_success(result['user'])
                )
            else:
                self.dialog.after(
                    0,
                    lambda: self._on_password_error(result['error'])
                )

        except Exception as e:
            self.dialog.after(
                0,
                lambda: self._on_password_error(str(e))
            )

    async def _sign_in_with_password(self, password: str) -> dict:
        """Sign in with 2FA password"""
        try:
            if not self.client:
                return {'success': False, 'error': 'Client not connected'}

            user = await self.client.sign_in(password=password)

            return {
                'success': True,
                'user': user.first_name
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid password: {str(e)}'
            }

    def _on_password_error(self, error: str) -> None:
        """Handle password error"""
        self._set_status(f"❌ {error}", True)
        self.password_btn.config(state=tk.NORMAL)
        self.password_entry.config(state=tk.NORMAL)
        self.password_var.set("")
        self.password_entry.focus_set()

    def _on_login_success(self, user_name: str) -> None:
        """Handle successful login"""
        self._set_status(f"✅ Successfully logged in as {user_name}!")

        # Disconnect client
        if self.client and self.loop:
            try:
                self.loop.run_until_complete(self.client.disconnect())
            except:
                pass

        # Close dialog after short delay
        self.dialog.after(1500, self._close_success, user_name)

    def _close_success(self, user_name: str) -> None:
        """Close dialog after successful login"""
        self.dialog.destroy()

        if self.on_success:
            self.on_success(user_name)

    def _on_close(self) -> None:
        """Handle dialog close"""
        # Disconnect client if connected
        if self.client and self.loop:
            try:
                async def disconnect():
                    if self.client.is_connected():
                        await self.client.disconnect()

                self.loop.run_until_complete(disconnect())
            except:
                pass

        self.dialog.destroy()

        if self.on_failure:
            self.on_failure("Login cancelled")


def show_login_dialog(
        parent: tk.Tk,
        api_id: int,
        api_hash: str,
        session_name: str,
        on_success: Optional[Callable[[str], None]] = None,
        on_failure: Optional[Callable[[str], None]] = None
) -> None:
    """
    Show the login dialog

    Args:
        parent: Parent window
        api_id: Telegram API ID
        api_hash: Telegram API Hash
        session_name: Session name to use
        on_success: Callback on successful login (receives user name)
        on_failure: Callback on failed login (receives error message)
    """
    LoginDialog(
        parent=parent,
        api_id=api_id,
        api_hash=api_hash,
        session_name=session_name,
        on_success=on_success,
        on_failure=on_failure
    )