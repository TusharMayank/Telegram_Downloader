"""
Application constants and default values
"""

# Application Info
APP_TITLE = "Telegram Media Downloader"
APP_GEOMETRY = "800x750"
APP_VERSION = "2.0.0"

# File paths
CONFIG_FILE = 'telegram_downloader_config.json'

# Default configuration
DEFAULT_CONFIG = {
    'api_id': '',
    'api_hash': '',
    'channel_id': '2299347106',
    'output_dir': 'downloads',
    'session_name': 'telegram_media_downloader'
}

# Supported audio extensions (kept for backwards compatibility)
AUDIO_EXTENSIONS = (
    '.mp3',
    '.m4a',
    '.wav',
    '.ogg',
    '.flac',
    '.aac',
    '.wma'
)

# MIME type to extension mapping
MIME_TO_EXTENSION = {
    'mp4': '.m4a',
    'm4a': '.m4a',
    'ogg': '.ogg',
    'wav': '.wav',
    'flac': '.flac',
    'aac': '.aac',
    'wma': '.wma'
}

# UI Constants
LOG_FONT = ('Consolas', 9)
ENTRY_FONT = ('Arial', 12)
BOLD_FONT = ('Arial', 10, 'bold')