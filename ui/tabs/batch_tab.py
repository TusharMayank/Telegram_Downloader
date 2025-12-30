"""
Batch download tab UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
from typing import List

from core.downloader import AudioDownloader
from ui.components.media_type_selector import MediaTypeSelector
from utils.media_types import MediaType


class BatchTab:
    """Batch download tab"""

    def __init__(self, parent, shared_vars, logger, app):
        self.parent = parent
        self.shared_vars = shared_vars
        self.logger = logger
        self.app = app

        # Selected media types
        self.selected_media_types: List[MediaType] = [MediaType.AUDIO]

        self.frame = ttk.Frame(parent, padding="10")
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create tab widgets"""
        # Range Download
        range_frame = ttk.LabelFrame(
            self.frame,
            text="Download Range",
            padding="10"
        )
        range_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(range_frame, text="From Post:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        ttk.Entry(
            range_frame,
            textvariable=self.shared_vars['range_from'],
            width=15
        ).grid(row=0, column=1, padx=5)

        ttk.Label(range_frame, text="To Post:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        ttk.Entry(
            range_frame,
            textvariable=self.shared_vars['range_to'],
            width=15
        ).grid(row=0, column=3, padx=5)

        self.range_btn = ttk.Button(
            range_frame,
            text="📥 Download Range",
            command=self._start_range_download
        )
        self.range_btn.grid(row=0, column=4, padx=10)

        # Multiple Posts
        multi_frame = ttk.LabelFrame(
            self.frame,
            text="Download Multiple Posts (comma-separated)",
            padding="10"
        )
        multi_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(
            multi_frame,
            textvariable=self.shared_vars['multi_posts'],
            width=60
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.multi_btn = ttk.Button(
            multi_frame,
            text="📥 Download All",
            command=self._start_multi_download
        )
        self.multi_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(
            multi_frame,
            text="e.g., 2436, 2437, 2440"
        ).pack(side=tk.LEFT, padx=5)

        # Sequential Download
        skip_frame = ttk.LabelFrame(
            self.frame,
            text="Sequential Download with Skip",
            padding="10"
        )
        skip_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(skip_frame, text="Skip first N files:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        ttk.Entry(
            skip_frame,
            textvariable=self.shared_vars['skip_count'],
            width=10
        ).grid(row=0, column=1, padx=5)

        ttk.Label(skip_frame, text="Max to download:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        ttk.Entry(
            skip_frame,
            textvariable=self.shared_vars['max_download'],
            width=10
        ).grid(row=0, column=3, padx=5)

        self.sequential_btn = ttk.Button(
            skip_frame,
            text="📥 Start Sequential Download",
            command=self._start_sequential_download
        )
        self.sequential_btn.grid(row=0, column=4, padx=10)

        # Media Type Selector (NEW!)
        self.media_selector = MediaTypeSelector(
            self.frame,
            on_change=self._on_media_type_change
        )
        self.media_selector.frame.pack(fill=tk.X, pady=(0, 10))

        # Other Options
        options_frame = ttk.LabelFrame(
            self.frame,
            text="Download Options",
            padding="10"
        )
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            options_frame,
            text="Skip existing files",
            variable=self.shared_vars['skip_existing']
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            options_frame,
            text="Download oldest first",
            variable=self.shared_vars['reverse_order']
        ).pack(anchor=tk.W)

        # Batch Progress
        progress_frame = ttk.LabelFrame(
            self.frame,
            text="Batch Progress",
            padding="10"
        )
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Progressbar(
            progress_frame,
            variable=self.shared_vars['batch_progress'],
            maximum=100
        ).pack(fill=tk.X, pady=5)

        ttk.Label(
            progress_frame,
            textvariable=self.shared_vars['batch_status']
        ).pack(anchor=tk.W)

    def _on_media_type_change(self, selected_types: List[MediaType]) -> None:
        """Handle media type selection change"""
        self.selected_media_types = selected_types

        type_names = [t.value for t in selected_types]
        self.logger.log(f"📋 Media types selected: {', '.join(type_names) if type_names else 'None'}")

    def _validate_media_selection(self) -> bool:
        """Validate that at least one media type is selected"""
        if not self.selected_media_types:
            messagebox.showwarning(
                "Warning",
                "Please select at least one media type to download"
            )
            return False
        return True

    def _start_range_download(self) -> None:
        """Start range download"""
        if not self.app.validate_settings():
            return

        if not self._validate_media_selection():
            return

        try:
            from_post = int(self.shared_vars['range_from'].get().strip())
            to_post = int(self.shared_vars['range_to'].get().strip())

            if from_post > to_post:
                from_post, to_post = to_post, from_post

            post_ids = list(range(from_post, to_post + 1))
            self.logger.log(f"Preparing to download {len(post_ids)} posts ({from_post} to {to_post})")

            self._download_posts(post_ids)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid post numbers")

    def _start_multi_download(self) -> None:
        """Start multiple posts download"""
        if not self.app.validate_settings():
            return

        if not self._validate_media_selection():
            return

        posts_str = self.shared_vars['multi_posts'].get().strip()

        if not posts_str:
            messagebox.showwarning("Warning", "Please enter post numbers")
            return

        try:
            post_ids = [
                int(p.strip())
                for p in posts_str.split(',')
                if p.strip()
            ]
            self.logger.log(f"Preparing to download {len(post_ids)} posts")
            self._download_posts(post_ids)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter valid comma-separated post numbers"
            )

    def _start_sequential_download(self) -> None:
        """Start sequential download"""
        if not self.app.validate_settings():
            return

        if not self._validate_media_selection():
            return

        try:
            skip_count = int(self.shared_vars['skip_count'].get().strip())
            max_download = int(self.shared_vars['max_download'].get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return

        self.app.stop_flag = False

        thread = threading.Thread(
            target=self._run_sequential_download,
            args=(skip_count, max_download),
            daemon=True
        )
        thread.start()

        self.app.set_downloading_state(True)

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
        """Run download process with parallel downloader"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from core.parallel_downloader import ParallelDownloader, DownloadProgress
            from config.performance import PerformanceConfigManager

            # Get performance config
            perf_config = PerformanceConfigManager().config

            # Progress callback
            def on_progress(progress: DownloadProgress):
                self.shared_vars['batch_progress'].set(progress.overall_progress)

                speed_mb = progress.download_speed / (1024 * 1024)
                status = f"Downloaded {progress.completed_files}/{progress.total_files}"

                if speed_mb > 0:
                    status += f" | {speed_mb:.2f} MB/s"

                self.shared_vars['batch_status'].set(status)

            downloader = ParallelDownloader(
                api_id=int(self.shared_vars['api_id'].get()),
                api_hash=self.shared_vars['api_hash'].get(),
                session_name=self.shared_vars['session_name'].get(),
                channel_id=self.shared_vars['channel_id'].get(),
                output_dir=self.shared_vars['output_dir'].get(),
                performance_config=perf_config,
                log_callback=self.logger.log,
                progress_callback=on_progress,
                status_callback=lambda s: self.shared_vars['batch_status'].set(s)
            )

            # Set media types
            downloader.media_types = self.selected_media_types
            downloader.skip_existing = self.shared_vars['skip_existing'].get()

            loop.run_until_complete(downloader.download_posts(post_ids))

        except Exception as e:
            self.logger.log(f"❌ Error: {str(e)}")
        finally:
            loop.close()
            self.frame.after(0, lambda: self.app.set_downloading_state(False))

    def _run_sequential_download(self, skip_count, max_download) -> None:
        """Run sequential download with parallel downloader"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from core.parallel_downloader import ParallelDownloader, DownloadProgress
            from config.performance import PerformanceConfigManager

            # Get performance config
            perf_config = PerformanceConfigManager().config

            # Progress callback
            def on_progress(progress: DownloadProgress):
                self.shared_vars['batch_progress'].set(progress.overall_progress)

                speed_mb = progress.download_speed / (1024 * 1024)
                status = f"Downloaded {progress.completed_files}/{progress.total_files}"

                if speed_mb > 0:
                    status += f" | {speed_mb:.2f} MB/s"

                self.shared_vars['batch_status'].set(status)

            downloader = ParallelDownloader(
                api_id=int(self.shared_vars['api_id'].get()),
                api_hash=self.shared_vars['api_hash'].get(),
                session_name=self.shared_vars['session_name'].get(),
                channel_id=self.shared_vars['channel_id'].get(),
                output_dir=self.shared_vars['output_dir'].get(),
                performance_config=perf_config,
                log_callback=self.logger.log,
                progress_callback=on_progress,
                status_callback=lambda s: self.shared_vars['batch_status'].set(s)
            )

            # Set media types
            downloader.media_types = self.selected_media_types
            downloader.skip_existing = self.shared_vars['skip_existing'].get()

            loop.run_until_complete(
                downloader.download_sequential(
                    skip_count,
                    max_download,
                    reverse=self.shared_vars['reverse_order'].get()
                )
            )

        except Exception as e:
            self.logger.log(f"❌ Error: {str(e)}")
        finally:
            loop.close()
            self.frame.after(0, lambda: self.app.set_downloading_state(False))

    def set_downloading_state(self, is_downloading: bool) -> None:
        """Update button states"""
        state = tk.DISABLED if is_downloading else tk.NORMAL
        self.range_btn.config(state=state)
        self.multi_btn.config(state=state)
        self.sequential_btn.config(state=state)