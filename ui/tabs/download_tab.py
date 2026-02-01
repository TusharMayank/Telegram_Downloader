"""
Download tab UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio

from core.downloader import AudioDownloader
from utils.helpers import parse_telegram_url, open_folder
from utils.constants import ENTRY_FONT


class DownloadTab:
    """Download tab for single post downloads"""

    def __init__(self, parent, shared_vars, logger, app):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Active Session Display
        session_frame = ttk.LabelFrame(
            self.frame,
            text="Active Session",
            padding="10"
        )
        session_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            session_frame,
            textvariable=self.shared_vars['active_session'],
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT)

        ttk.Button(
            session_frame,
            text="🔌 Check Connection",
            command=self._test_connection
        ).pack(side=tk.RIGHT, padx=5)

        # Post Number Input
        input_frame = ttk.LabelFrame(
            self.frame,
            text="Single Post Download",
            padding="10"
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Post Number:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )

        post_entry = ttk.Entry(
            input_frame,
            textvariable=self.shared_vars['post_number'],
            width=20,
            font=ENTRY_FONT
        )
        post_entry.grid(row=0, column=1, padx=5, pady=5)
        post_entry.bind('<Return>', lambda e: self._start_download())

        ttk.Label(
            input_frame,
            text="(e.g., 2436 from https://t.me/c/2299347106/2436)"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)

        self.download_btn = ttk.Button(
            input_frame,
            text="📥 Download Post",
            command=self._start_download
        )
        self.download_btn.grid(row=0, column=3, padx=10)

        # URL Parser
        url_frame = ttk.LabelFrame(
            self.frame,
            text="Or Paste Full URL",
            padding="10"
        )
        url_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(
            url_frame,
            textvariable=self.shared_vars['url'],
            width=60
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            url_frame,
            text="Parse & Download",
            command=self._parse_url_and_download
        ).pack(side=tk.LEFT, padx=5)

        # Output Directory
        dir_frame = ttk.LabelFrame(
            self.frame,
            text="Output Directory",
            padding="10"
        )
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(
            dir_frame,
            textvariable=self.shared_vars['output_dir'],
            width=50
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            dir_frame,
            text="Browse...",
            command=self._browse_output_dir
        ).pack(side=tk.LEFT, padx=5)

        # Progress
        progress_frame = ttk.LabelFrame(
            self.frame,
            text="Progress",
            padding="10"
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Progressbar(
            progress_frame,
            variable=self.shared_vars['progress'],
            maximum=100
        ).pack(fill=tk.X, pady=5)

        ttk.Label(
            progress_frame,
            textvariable=self.shared_vars['status']
        ).pack(anchor=tk.W)

        # Log
        log_frame = ttk.LabelFrame(self.frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.logger.create_widget(log_frame).pack(fill=tk.BOTH, expand=True)

        # Control Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X)

        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹️ Stop",
            command=self._stop_download,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🗑️ Clear Log",
            command=self.logger.clear
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="📂 Open Downloads Folder",
            command=self._open_downloads_folder
        ).pack(side=tk.RIGHT, padx=5)

    def _browse_output_dir(self) -> None:
        """Browse for output directory"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(
            initialdir=self.shared_vars['output_dir'].get()
        )
        if directory:
            self.shared_vars['output_dir'].set(directory)
            # Save the new directory to configuration immediately
            self.app.config_manager.set('output_dir', directory)
            self.app.config_manager.save(self.app.config_manager.config)

    def _open_downloads_folder(self) -> None:
        """Open downloads folder"""
        open_folder(self.shared_vars['output_dir'].get())

    def _parse_url_and_download(self) -> None:
        """Parse URL and start download"""
        url = self.shared_vars['url'].get().strip()

        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        channel_id, post_number = parse_telegram_url(url)

        if channel_id and post_number:
            self.shared_vars['channel_id'].set(channel_id)
            self.shared_vars['post_number'].set(post_number)
            self.logger.log(f"Parsed URL - Channel: {channel_id}, Post: {post_number}")
            self._start_download()
        else:
            messagebox.showerror(
                "Error",
                "Invalid URL format. Expected: https://t.me/c/CHANNEL_ID/POST_NUMBER"
            )

    def _start_download(self) -> None:
        """Start single post download"""
        if not self.app.validate_settings():
            return

        post_number = self.shared_vars['post_number'].get().strip()

        if not post_number:
            messagebox.showwarning("Warning", "Please enter a post number")
            return

        try:
            post_id = int(post_number)
        except ValueError:
            messagebox.showerror("Error", "Post number must be a valid integer")
            return

        self._download_posts([post_id])

    def _download_posts(self, post_ids) -> None:
        """Start download in separate thread"""
        self.app.stop_flag = False

        thread = threading.Thread(
            target=self._run_download,
            args=(post_ids,),
            daemon=True
        )
        thread.start()

        self.app.set_downloading_state(True)

    def _run_download(self, post_ids) -> None:
        """Run download process"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            downloader = AudioDownloader(
                api_id=int(self.shared_vars['api_id'].get()),
                api_hash=self.shared_vars['api_hash'].get(),
                session_name=self.shared_vars['session_name'].get(),
                channel_id=self.shared_vars['channel_id'].get(),
                output_dir=self.shared_vars['output_dir'].get(),
                log_callback=self.logger.log,
                progress_callback=lambda p: self.shared_vars['progress'].set(p),
                status_callback=lambda s: self.shared_vars['status'].set(s)
            )

            downloader.audio_only = self.shared_vars['audio_only'].get()
            downloader.skip_existing = self.shared_vars['skip_existing'].get()

            loop.run_until_complete(downloader.download_posts(post_ids))

        except Exception as e:
            self.logger.log(f"❌ Error: {str(e)}")
        finally:
            loop.close()
            self.frame.after(0, lambda: self.app.set_downloading_state(False))

    def _stop_download(self) -> None:
        """Stop current download"""
        self.app.stop_flag = True
        self.logger.log("🛑 Stop requested...")
        self.shared_vars['status'].set("Stopping...")

    def _test_connection(self) -> None:
        """Test Telegram connection"""
        if not self.app.validate_settings():
            return

        from core.client import TelegramClientWrapper

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

                    if info['authorized']:
                        return f"✅ Connected as {info['info']}", info['info']
                    else:
                        return "⚠️ Not logged in", None

                result, name = loop.run_until_complete(test())

                self.frame.after(0, lambda: self.logger.log(result))

                if name:
                    session = self.shared_vars['session_name'].get()
                    self.frame.after(
                        0,
                        lambda: self.shared_vars['active_session'].set(
                            f"Session: {session} - 👤 {name}"
                        )
                    )

            except Exception as e:
                self.frame.after(0, lambda: self.logger.log(f"❌ Error: {str(e)}"))
            finally:
                loop.close()

        threading.Thread(target=run_test, daemon=True).start()

    def set_downloading_state(self, is_downloading: bool) -> None:
        """Update button states"""
        state = tk.DISABLED if is_downloading else tk.NORMAL
        self.download_btn.config(state=state)
        self.stop_btn.config(state=tk.NORMAL if is_downloading else tk.DISABLED)