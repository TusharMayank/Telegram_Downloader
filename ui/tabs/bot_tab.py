"""
Chat Downloads tab UI
Download media from any Telegram chat (bots, users, groups)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
from typing import List, Optional

from core.bot_downloader import BotDownloader, BotDownloadProgress, BotDownloadStatus
from utils.bot_helpers import BotChatStats, parse_bot_username
from utils.media_types import MediaType
from utils.helpers import open_folder


class BotTab:
    """Chat downloads tab - works with bots, users, and groups"""

    def __init__(self, parent, shared_vars, logger, app):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app

        # Tab-specific variables
        self.bot_vars = self._create_variables()

        # State
        self.downloader: Optional[BotDownloader] = None
        self.chat_stats: Optional[BotChatStats] = None
        self.is_downloading = False

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

    def _create_variables(self) -> dict:
        """Create tab-specific variables"""
        return {
            'chat_username': tk.StringVar(),
            'chat_type': tk.StringVar(value='bot'),
            'chat_status': tk.StringVar(value="Enter a username or chat ID to start"),
            'output_dir': self.shared_vars['output_dir'],
            'create_subfolder': tk.BooleanVar(value=True),
            'skip_existing': tk.BooleanVar(value=True),
            'oldest_first': tk.BooleanVar(value=False),
            'download_range': tk.StringVar(value='all'),
            'first_n_files': tk.StringVar(value="100"),
            'last_n_files': tk.StringVar(value="100"),
            'skip_first_n': tk.StringVar(value="0"),
            'range_from': tk.StringVar(value="1"),
            'range_to': tk.StringVar(value="100"),

            # Stats display
            'total_messages': tk.StringVar(value="-"),
            'audio_count': tk.StringVar(value="-"),
            'video_count': tk.StringVar(value="-"),
            'photo_count': tk.StringVar(value="-"),
            'document_count': tk.StringVar(value="-"),
            'voice_count': tk.StringVar(value="-"),
            'total_media': tk.StringVar(value="-"),

            # Progress
            'progress': tk.DoubleVar(value=0),
            'status_text': tk.StringVar(value="Ready"),
            'current_file': tk.StringVar(value=""),
            'speed': tk.StringVar(value=""),

            # Media type selections
            'select_audio': tk.BooleanVar(value=True),
            'select_video': tk.BooleanVar(value=False),
            'select_photo': tk.BooleanVar(value=False),
            'select_document': tk.BooleanVar(value=False),
            'select_voice': tk.BooleanVar(value=False),
        }

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Create scrollable frame
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", configure_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll function
        def _on_scroll(event):
            if canvas.yview() == (0.0, 1.0):
                return
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                if event.delta != 0:
                    scroll_units = int(-1 * (event.delta / 120)) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
                    canvas.yview_scroll(scroll_units, "units")

        def bind_scroll(widget):
            widget.bind("<MouseWheel>", _on_scroll, add="+")
            widget.bind("<Button-4>", _on_scroll, add="+")
            widget.bind("<Button-5>", _on_scroll, add="+")
            for child in widget.winfo_children():
                bind_scroll(child)

        bind_scroll(canvas)
        bind_scroll(scrollable_frame)

        # === Chat Type Selection ===
        type_frame = ttk.LabelFrame(
            scrollable_frame,
            text="💬 Chat Type",
            padding="10"
        )
        type_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        type_btn_frame = ttk.Frame(type_frame)
        type_btn_frame.pack(fill=tk.X)

        ttk.Radiobutton(
            type_btn_frame,
            text="🤖 Bot",
            variable=self.bot_vars['chat_type'],
            value='bot',
            command=self._on_chat_type_change
        ).pack(side=tk.LEFT, padx=10)

        ttk.Radiobutton(
            type_btn_frame,
            text="👤 Private Chat (User)",
            variable=self.bot_vars['chat_type'],
            value='user',
            command=self._on_chat_type_change
        ).pack(side=tk.LEFT, padx=10)

        ttk.Radiobutton(
            type_btn_frame,
            text="👥 Group Chat",
            variable=self.bot_vars['chat_type'],
            value='group',
            command=self._on_chat_type_change
        ).pack(side=tk.LEFT, padx=10)

        # Help text
        self.help_text_var = tk.StringVar(value="Enter bot username (e.g., @MusicBot or MusicBot)")
        ttk.Label(
            type_frame,
            textvariable=self.help_text_var,
            foreground="gray",
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=(10, 0))

        # === Chat Configuration ===
        chat_frame = ttk.LabelFrame(
            scrollable_frame,
            text="💬 Chat Configuration",
            padding="10"
        )
        chat_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X)

        self.input_label = ttk.Label(input_frame, text="Username/ID:")
        self.input_label.pack(side=tk.LEFT)

        self.at_label = ttk.Label(input_frame, text="@", font=('Arial', 11))
        self.at_label.pack(side=tk.LEFT, padx=(10, 0))

        self.username_entry = ttk.Entry(
            input_frame,
            textvariable=self.bot_vars['chat_username'],
            width=30,
            font=('Arial', 11)
        )
        self.username_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.username_entry.bind('<Return>', lambda e: self._scan_chat())

        self.scan_btn = ttk.Button(
            input_frame,
            text="🔍 Scan Chat",
            command=self._scan_chat
        )
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        # Status
        ttk.Label(
            chat_frame,
            textvariable=self.bot_vars['chat_status'],
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=(10, 0))

        # === Scan Results ===
        stats_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📊 Scan Results",
            padding="10"
        )
        stats_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Stats grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        stats_items = [
            ("Total messages:", 'total_messages', 0, 0),
            ("🎵 Audio files:", 'audio_count', 1, 0),
            ("🎬 Video files:", 'video_count', 2, 0),
            ("🖼️ Photos:", 'photo_count', 3, 0),
            ("📄 Documents:", 'document_count', 1, 2),
            ("🎤 Voice messages:", 'voice_count', 2, 2),
            ("📁 Total media:", 'total_media', 3, 2),
        ]

        for label, var_name, row, col in stats_items:
            ttk.Label(stats_grid, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            ttk.Label(
                stats_grid,
                textvariable=self.bot_vars[var_name],
                font=('Arial', 10, 'bold')
            ).grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)

        # === Download Options ===
        options_frame = ttk.LabelFrame(
            scrollable_frame,
            text="⚙️ Download Options",
            padding="10"
        )
        options_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Media type selection
        ttk.Label(options_frame, text="Media types to download:").pack(anchor=tk.W)

        media_frame = ttk.Frame(options_frame)
        media_frame.pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            media_frame,
            text="🎵 Audio (.mp3, .m4a, .flac, .wav)",
            variable=self.bot_vars['select_audio']
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        ttk.Checkbutton(
            media_frame,
            text="🎬 Video (.mp4, .mkv, .avi)",
            variable=self.bot_vars['select_video']
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Checkbutton(
            media_frame,
            text="🖼️ Photos (.jpg, .png)",
            variable=self.bot_vars['select_photo']
        ).grid(row=1, column=0, sticky=tk.W, padx=5)

        ttk.Checkbutton(
            media_frame,
            text="📄 Documents",
            variable=self.bot_vars['select_document']
        ).grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Checkbutton(
            media_frame,
            text="🎤 Voice messages",
            variable=self.bot_vars['select_voice']
        ).grid(row=2, column=0, sticky=tk.W, padx=5)

        # Download range
        ttk.Separator(options_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(options_frame, text="Download range:").pack(anchor=tk.W)

        range_frame = ttk.Frame(options_frame)
        range_frame.pack(fill=tk.X, pady=5)

        # Row 0: All files
        ttk.Radiobutton(
            range_frame,
            text="All files",
            variable=self.bot_vars['download_range'],
            value='all'
        ).grid(row=0, column=0, sticky=tk.W, padx=5, columnspan=4)

        # Row 1: First N files (oldest)
        ttk.Radiobutton(
            range_frame,
            text="First",
            variable=self.bot_vars['download_range'],
            value='first_n'
        ).grid(row=1, column=0, sticky=tk.W, padx=5)

        ttk.Entry(
            range_frame,
            textvariable=self.bot_vars['first_n_files'],
            width=8
        ).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(range_frame, text="files (oldest)").grid(row=1, column=2, sticky=tk.W, padx=5)

        # Row 2: Last N files (newest)
        ttk.Radiobutton(
            range_frame,
            text="Last",
            variable=self.bot_vars['download_range'],
            value='last_n'
        ).grid(row=2, column=0, sticky=tk.W, padx=5)

        ttk.Entry(
            range_frame,
            textvariable=self.bot_vars['last_n_files'],
            width=8
        ).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(range_frame, text="files (newest)").grid(row=2, column=2, sticky=tk.W, padx=5)

        # Row 3: Skip first N
        ttk.Radiobutton(
            range_frame,
            text="Skip first",
            variable=self.bot_vars['download_range'],
            value='skip_n'
        ).grid(row=3, column=0, sticky=tk.W, padx=5)

        ttk.Entry(
            range_frame,
            textvariable=self.bot_vars['skip_first_n'],
            width=8
        ).grid(row=3, column=1, sticky=tk.W)

        ttk.Label(range_frame, text="files, then download all").grid(row=3, column=2, sticky=tk.W, padx=5)

        # Row 4: Custom range (First N to Last M)
        ttk.Radiobutton(
            range_frame,
            text="Custom range: from file",
            variable=self.bot_vars['download_range'],
            value='custom_range'
        ).grid(row=4, column=0, sticky=tk.W, padx=5)

        self.bot_vars['range_from'] = tk.StringVar(value="1")
        self.bot_vars['range_to'] = tk.StringVar(value="100")

        ttk.Entry(
            range_frame,
            textvariable=self.bot_vars['range_from'],
            width=6
        ).grid(row=4, column=1, sticky=tk.W)

        ttk.Label(range_frame, text="to").grid(row=4, column=2, sticky=tk.W, padx=2)

        ttk.Entry(
            range_frame,
            textvariable=self.bot_vars['range_to'],
            width=6
        ).grid(row=4, column=3, sticky=tk.W)

        # Other options
        ttk.Separator(options_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Checkbutton(
            options_frame,
            text="Skip existing files",
            variable=self.bot_vars['skip_existing']
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options_frame,
            text="Download oldest first",
            variable=self.bot_vars['oldest_first']
        ).pack(anchor=tk.W)

        # === Output Directory ===
        output_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📂 Output Directory",
            padding="10"
        )
        output_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill=tk.X)

        ttk.Entry(
            dir_frame,
            textvariable=self.bot_vars['output_dir'],
            width=50
        ).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        ttk.Button(
            dir_frame,
            text="Browse...",
            command=self._browse_output_dir
        ).pack(side=tk.LEFT)

        ttk.Checkbutton(
            output_frame,
            text="Create subfolder with chat name",
            variable=self.bot_vars['create_subfolder']
        ).pack(anchor=tk.W, pady=(10, 0))

        # === Download Controls ===
        download_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📥 Download",
            padding="10"
        )
        download_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        btn_frame = ttk.Frame(download_frame)
        btn_frame.pack(fill=tk.X)

        self.download_btn = ttk.Button(
            btn_frame,
            text="📥 Start Download",
            command=self._start_download
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹️ Stop",
            command=self._stop_download,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="📂 Open Folder",
            command=self._open_output_folder
        ).pack(side=tk.LEFT, padx=5)

        # Progress bar
        ttk.Progressbar(
            download_frame,
            variable=self.bot_vars['progress'],
            maximum=100
        ).pack(fill=tk.X, pady=(10, 5))

        # Status text
        status_frame = ttk.Frame(download_frame)
        status_frame.pack(fill=tk.X)

        ttk.Label(
            status_frame,
            textvariable=self.bot_vars['status_text']
        ).pack(side=tk.LEFT)

        ttk.Label(
            status_frame,
            textvariable=self.bot_vars['speed'],
            foreground="blue"
        ).pack(side=tk.RIGHT)

        ttk.Label(
            download_frame,
            textvariable=self.bot_vars['current_file'],
            foreground="gray"
        ).pack(anchor=tk.W)

        # === Info Box ===
        info_frame = ttk.LabelFrame(
            scrollable_frame,
            text="ℹ️ Supported Chat Types",
            padding="10"
        )
        info_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        info_text = """
🤖 Bot: Download files that a bot has sent to you
   Example: @MusicBot, @FileStoreBot

👤 Private Chat: Download files from chat with a friend
   Example: @username or phone number

👥 Group Chat: Download files from a group you're in
   Example: Group username or invite link ID

Note: You can only download files from chats you have access to.
        """

        ttk.Label(
            info_frame,
            text=info_text,
            justify=tk.LEFT,
            font=('Arial', 9)
        ).pack(anchor=tk.W)

        # === Log ===
        log_frame = ttk.LabelFrame(
            scrollable_frame,
            text="📋 Log",
            padding="10"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)

        self.log_widget = self.logger.create_widget(log_frame)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        # Bind scroll to all
        bind_scroll(scrollable_frame)

    def _on_chat_type_change(self) -> None:
        """Update UI when chat type changes"""
        chat_type = self.bot_vars['chat_type'].get()

        if chat_type == 'bot':
            self.help_text_var.set("Enter bot username (e.g., @MusicBot or MusicBot)")
            self.input_label.config(text="Bot Username:")
            self.at_label.pack(side=tk.LEFT, padx=(10, 0))
        elif chat_type == 'user':
            self.help_text_var.set("Enter username (e.g., @friend) or phone number (e.g., +1234567890)")
            self.input_label.config(text="Username/Phone:")
            self.at_label.pack_forget()
        elif chat_type == 'group':
            self.help_text_var.set("Enter group username (e.g., @groupname) or group ID")
            self.input_label.config(text="Group Username/ID:")
            self.at_label.pack_forget()

        # Reset stats when changing type
        self._reset_stats()

    def _reset_stats(self) -> None:
        """Reset stats display"""
        self.chat_stats = None
        self.bot_vars['total_messages'].set("-")
        self.bot_vars['audio_count'].set("-")
        self.bot_vars['video_count'].set("-")
        self.bot_vars['photo_count'].set("-")
        self.bot_vars['document_count'].set("-")
        self.bot_vars['voice_count'].set("-")
        self.bot_vars['total_media'].set("-")
        self.bot_vars['chat_status'].set("Enter a username or chat ID to start")

    def _browse_output_dir(self) -> None:
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            initialdir=self.bot_vars['output_dir'].get()
        )
        if directory:
            self.bot_vars['output_dir'].set(directory)

    def _open_output_folder(self) -> None:
        """Open output folder"""
        output_dir = self.bot_vars['output_dir'].get()
        chat_name = self.bot_vars['chat_username'].get().strip().replace('@', '')

        if self.bot_vars['create_subfolder'].get() and chat_name:
            output_dir = os.path.join(output_dir, chat_name)

        if os.path.exists(output_dir):
            open_folder(output_dir)
        else:
            open_folder(self.bot_vars['output_dir'].get())

    def _get_selected_media_types(self) -> List[MediaType]:
        """Get list of selected media types"""
        types = []

        if self.bot_vars['select_audio'].get():
            types.append(MediaType.AUDIO)
        if self.bot_vars['select_video'].get():
            types.append(MediaType.VIDEO)
        if self.bot_vars['select_photo'].get():
            types.append(MediaType.PHOTO)
        if self.bot_vars['select_document'].get():
            types.append(MediaType.DOCUMENT)
        if self.bot_vars['select_voice'].get():
            types.append(MediaType.VOICE)

        return types

    def _get_chat_identifier(self) -> str:
        """Get the chat identifier based on type and input"""
        chat_input = self.bot_vars['chat_username'].get().strip()
        chat_type = self.bot_vars['chat_type'].get()

        # Clean up input
        if chat_input.startswith('@'):
            chat_input = chat_input[1:]

        # For bot type, we might want to add @ back
        # For user/group, could be username, phone, or ID

        return chat_input

    def _validate_inputs(self) -> bool:
        """Validate user inputs"""
        # Check chat identifier
        chat_input = self.bot_vars['chat_username'].get().strip()
        if not chat_input:
            messagebox.showwarning("Warning", "Please enter a username or chat ID")
            return False

        # Check media types
        if not self._get_selected_media_types():
            messagebox.showwarning("Warning", "Please select at least one media type")
            return False

        # Check API credentials
        if not self.app.validate_settings():
            return False

        return True

    def _scan_chat(self) -> None:
        """Scan chat history"""
        if not self._validate_inputs():
            return

        self._reset_stats()
        self.bot_vars['chat_status'].set("Scanning...")
        self._set_scanning_state(True)

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self) -> None:
        """Run scan in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from config.performance import PerformanceConfigManager

            # Create new downloader for scanning
            self.downloader = BotDownloader(
                api_id=int(self.shared_vars['api_id'].get()),
                api_hash=self.shared_vars['api_hash'].get(),
                session_name=self.shared_vars['session_name'].get(),
                output_dir=self.bot_vars['output_dir'].get(),
                performance_config=PerformanceConfigManager().config,
                log_callback=self.logger.log,
                progress_callback=self._on_progress,
                stats_callback=self._on_stats
            )

            chat_identifier = self._get_chat_identifier()
            chat_type = self.bot_vars['chat_type'].get()

            self.logger.log(f"📋 Chat type: {chat_type}")

            stats = loop.run_until_complete(self.downloader.scan_chat(chat_identifier))

            if stats:
                self.chat_stats = stats
                self.frame.after(0, lambda: self.bot_vars['chat_status'].set(
                    f"✅ Scan complete! Found {stats.total_media} media files"
                ))
            else:
                self.frame.after(0, lambda: self.bot_vars['chat_status'].set(
                    "❌ Scan failed. Check log for details."
                ))

        except Exception as e:
            self.logger.log(f"❌ Error: {str(e)}")
            self.frame.after(0, lambda: self.bot_vars['chat_status'].set(f"❌ Error: {str(e)}"))
        finally:
            # Disconnect after scan to prevent database lock
            if self.downloader:
                try:
                    loop.run_until_complete(self.downloader.disconnect())
                except:
                    pass
            loop.close()
            self.frame.after(0, lambda: self._set_scanning_state(False))

    def _on_stats(self, stats: BotChatStats) -> None:
        """Update stats display"""
        self.frame.after(0, lambda: self._update_stats_display(stats))

    def _update_stats_display(self, stats: BotChatStats) -> None:
        """Update stats labels"""
        self.bot_vars['total_messages'].set(str(stats.total_messages))
        self.bot_vars['audio_count'].set(str(stats.audio_count))
        self.bot_vars['video_count'].set(str(stats.video_count))
        self.bot_vars['photo_count'].set(str(stats.photo_count))
        self.bot_vars['document_count'].set(str(stats.document_count))
        self.bot_vars['voice_count'].set(str(stats.voice_count))
        self.bot_vars['total_media'].set(str(stats.total_media))

    def _on_progress(self, progress: BotDownloadProgress) -> None:
        """Update progress display"""
        self.frame.after(0, lambda: self._update_progress_display(progress))

    def _update_progress_display(self, progress: BotDownloadProgress) -> None:
        """Update progress labels with speed"""
        self.bot_vars['progress'].set(progress.overall_progress)

        # Status text
        status = f"Downloaded {progress.downloaded_files}"
        if progress.total_files > 0:
            status += f"/{progress.total_files}"
        if progress.skipped_files > 0:
            status += f" | Skipped: {progress.skipped_files}"
        if progress.failed_files > 0:
            status += f" | Failed: {progress.failed_files}"

        self.bot_vars['status_text'].set(status)

        # Current file
        if progress.current_file:
            file_progress = f" ({progress.current_file_progress:.0f}%)" if progress.current_file_progress > 0 else ""
            self.bot_vars['current_file'].set(f"📄 {progress.current_file}{file_progress}")

        # Speed display
        if progress.download_speed > 0:
            speed_mbps = progress.download_speed / (1024 * 1024)
            if speed_mbps >= 1:
                self.bot_vars['speed'].set(f"⚡ {speed_mbps:.2f} MB/s")
            else:
                speed_kbps = progress.download_speed / 1024
                self.bot_vars['speed'].set(f"⚡ {speed_kbps:.0f} KB/s")
        else:
            self.bot_vars['speed'].set("")

    def _start_download(self) -> None:
        """Start download"""
        if not self._validate_inputs():
            return

        self._set_downloading_state(True)

        thread = threading.Thread(target=self._run_download, daemon=True)
        thread.start()

    def _run_download(self) -> None:
        """Run download in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from config.performance import PerformanceConfigManager

            # Reuse existing downloader if available, otherwise create new
            if not self.downloader:
                self.downloader = BotDownloader(
                    api_id=int(self.shared_vars['api_id'].get()),
                    api_hash=self.shared_vars['api_hash'].get(),
                    session_name=self.shared_vars['session_name'].get(),
                    output_dir=self.bot_vars['output_dir'].get(),
                    performance_config=PerformanceConfigManager().config,
                    log_callback=self.logger.log,
                    progress_callback=self._on_progress,
                    stats_callback=self._on_stats
                )
            else:
                # Update output directory in case it changed
                self.downloader.output_dir = self.bot_vars['output_dir'].get()

            # Set options
            self.downloader.media_types = self._get_selected_media_types()
            self.downloader.skip_existing = self.bot_vars['skip_existing'].get()
            self.downloader.create_subfolder = self.bot_vars['create_subfolder'].get()
            self.downloader.download_oldest_first = self.bot_vars['oldest_first'].get()

            # Set range options
            range_type = self.bot_vars['download_range'].get()

            # Reset all range options
            self.downloader.max_download = 0
            self.downloader.skip_count = 0
            self.downloader.download_oldest_first = self.bot_vars['oldest_first'].get()

            if range_type == 'first_n':
                # First N files (oldest) - download oldest first, limit to N
                try:
                    self.downloader.max_download = int(self.bot_vars['first_n_files'].get())
                except ValueError:
                    self.downloader.max_download = 100
                self.downloader.download_oldest_first = True  # Force oldest first

            elif range_type == 'last_n':
                # Last N files (newest) - download newest first, limit to N
                try:
                    self.downloader.max_download = int(self.bot_vars['last_n_files'].get())
                except ValueError:
                    self.downloader.max_download = 100
                self.downloader.download_oldest_first = False  # Force newest first

            elif range_type == 'skip_n':
                # Skip first N, then download all remaining
                try:
                    self.downloader.skip_count = int(self.bot_vars['skip_first_n'].get())
                except ValueError:
                    self.downloader.skip_count = 0

            elif range_type == 'custom_range':
                # Custom range: from file X to file Y
                try:
                    range_from = int(self.bot_vars['range_from'].get())
                    range_to = int(self.bot_vars['range_to'].get())

                    # Skip files before range_from
                    self.downloader.skip_count = max(0, range_from - 1)
                    # Download only (range_to - range_from + 1) files
                    self.downloader.max_download = max(1, range_to - range_from + 1)
                    self.downloader.download_oldest_first = True  # Start from oldest

                except ValueError:
                    self.downloader.skip_count = 0
                    self.downloader.max_download = 100

            # Use existing stats if available
            if self.chat_stats:
                self.downloader.chat_stats = self.chat_stats

            chat_identifier = self._get_chat_identifier()

            # Download - don't scan again if we already have stats
            result = loop.run_until_complete(
                self.downloader.download_from_bot(chat_identifier, scan_first=not self.chat_stats)
            )

            self.frame.after(0, lambda: self.bot_vars['status_text'].set(
                f"✅ Complete! Downloaded: {result.get('downloaded', 0)}"
            ))

        except Exception as e:
            self.logger.log(f"❌ Error: {str(e)}")
        finally:
            # Disconnect after download
            if self.downloader:
                try:
                    loop.run_until_complete(self.downloader.disconnect())
                except:
                    pass

                # Check if stopped
                was_stopped = self.downloader.stop_flag

                if was_stopped:
                    self.frame.after(0, lambda: self.bot_vars['status_text'].set("⏹️ Stopped by user"))
                    self.frame.after(0, lambda: self.logger.log("⏹️ Download stopped by user"))

            loop.close()
            self.frame.after(0, lambda: self._set_downloading_state(False))

    def _stop_download(self) -> None:
        """Stop download immediately"""
        self.logger.log("🛑 Stopping download...")
        self.bot_vars['status_text'].set("Stopping...")

        if self.downloader:
            self.downloader.stop()

        # Update UI immediately
        self.stop_btn.config(state=tk.DISABLED)

    def _set_scanning_state(self, is_scanning: bool) -> None:
        """Update UI state during scanning"""
        state = tk.DISABLED if is_scanning else tk.NORMAL
        self.scan_btn.config(state=state)
        self.username_entry.config(state=state)

    def _set_downloading_state(self, is_downloading: bool) -> None:
        """Update UI state during download"""
        self.is_downloading = is_downloading

        if is_downloading:
            self.download_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.scan_btn.config(state=tk.DISABLED)
        else:
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.scan_btn.config(state=tk.NORMAL)