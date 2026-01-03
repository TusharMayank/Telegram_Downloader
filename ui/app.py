"""
Main application window
"""

import tkinter as tk
from tkinter import ttk

from config import ConfigManager
from utils.constants import APP_TITLE, APP_GEOMETRY
from .tabs.download_tab import DownloadTab
from .tabs.batch_tab import BatchTab
from .tabs.settings_tab import SettingsTab
from .components.logger import LoggerComponent


class TelegramAudioDownloaderApp:
    """Main application class"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)
        self.root.resizable(True, True)

        # Initialize configuration
        self.config_manager = ConfigManager()

        # Shared state
        self.is_downloading = False
        self.stop_flag = False
        self.session_accounts = {}

        # Shared variables (will be accessed by tabs)
        self.shared_vars = self._create_shared_vars()

        # Create UI
        self._create_ui()

        # Refresh sessions on startup
        self.root.after(500, self.settings_tab.refresh_sessions)

    def _create_shared_vars(self) -> dict:
        """Create shared Tkinter variables"""
        config = self.config_manager.config

        return {
            'api_id': tk.StringVar(value=config.get('api_id', '')),
            'api_hash': tk.StringVar(value=config.get('api_hash', '')),
            'channel_id': tk.StringVar(value=config.get('channel_id', '2299347106')),
            'output_dir': tk.StringVar(value=config.get('output_dir', 'downloads')),
            'session_name': tk.StringVar(value=config.get('session_name', 'telegram_audio_downloader')),
            'post_number': tk.StringVar(),
            'url': tk.StringVar(),
            'status': tk.StringVar(value="Ready"),
            'progress': tk.DoubleVar(),
            'active_session': tk.StringVar(value="No session active"),
            'connection_status': tk.StringVar(value="Not connected"),
            'session_info': tk.StringVar(value=""),

            # Batch tab variables
            'range_from': tk.StringVar(),
            'range_to': tk.StringVar(),
            'multi_posts': tk.StringVar(),
            'skip_count': tk.StringVar(value="0"),
            'max_download': tk.StringVar(value="100"),
            'batch_status': tk.StringVar(value="Ready for batch download"),
            'batch_progress': tk.DoubleVar(),

            # Options
            'audio_only': tk.BooleanVar(value=True),
            'skip_existing': tk.BooleanVar(value=True),
            'reverse_order': tk.BooleanVar(value=False),
            'show_hash': tk.BooleanVar(value=False),

            # New session
            'new_session': tk.StringVar()
        }

    def _create_ui(self) -> None:
        """Create the main UI layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create logger component (shared across tabs)
        from ui.components.logger import LoggerComponent
        self.logger = LoggerComponent()

        # Import all tab classes
        from ui.tabs.download_tab import DownloadTab
        from ui.tabs.batch_tab import BatchTab
        from ui.tabs.bot_tab import BotTab
        from ui.tabs.performance_tab import PerformanceTab
        from ui.tabs.settings_tab import SettingsTab
        from ui.tabs.about_tab import AboutTab

        # Create tabs
        self.download_tab = DownloadTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self
        )

        self.batch_tab = BatchTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self
        )

        self.bot_tab = BotTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self
        )

        self.performance_tab = PerformanceTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self
        )

        self.settings_tab = SettingsTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self,
            self.config_manager
        )

        self.about_tab = AboutTab(
            self.notebook,
            self.shared_vars,
            self.logger,
            self
        )

        # Add tabs to notebook
        self.notebook.add(self.download_tab.frame, text="📥 Download")
        self.notebook.add(self.batch_tab.frame, text="📦 Batch Download")
        self.notebook.add(self.bot_tab.frame, text="💬 Chat Downloads")
        self.notebook.add(self.performance_tab.frame, text="⚡ Performance")
        self.notebook.add(self.settings_tab.frame, text="⚙️ Settings")
        self.notebook.add(self.about_tab.frame, text="ℹ️ About")

    def set_downloading_state(self, is_downloading: bool) -> None:
        """Update UI state based on download status"""
        self.is_downloading = is_downloading
        self.download_tab.set_downloading_state(is_downloading)
        self.batch_tab.set_downloading_state(is_downloading)

    def validate_settings(self) -> bool:
        """Validate API credentials"""
        api_id = self.shared_vars['api_id'].get().strip()
        api_hash = self.shared_vars['api_hash'].get().strip()

        if not api_id or not api_hash:
            from tkinter import messagebox
            messagebox.showerror(
                "Error",
                "Please enter your API ID and API Hash in the Settings tab"
            )
            self.notebook.select(self.settings_tab.frame)
            return False

        try:
            int(api_id)
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "API ID must be a number")
            return False

        return True