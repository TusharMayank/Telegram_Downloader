"""
Utility helper functions
"""

import os
import subprocess
import platform
from typing import Optional, Tuple
from .constants import MIME_TO_EXTENSION, AUDIO_EXTENSIONS


def parse_telegram_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a Telegram URL and extract channel ID and post number

    Args:
        url: Telegram URL (e.g., https://t.me/c/2299347106/2436)

    Returns:
        Tuple of (channel_id, post_number) or (None, None) if invalid
    """
    try:
        if '/c/' in url:
            parts = url.split('/c/')[1].split('/')
            channel_id = parts[0]
            post_number = parts[1].split('?')[0]  # Remove query params
            return channel_id, post_number
    except (IndexError, AttributeError):
        pass

    return None, None


def get_audio_extension(mime_type: Optional[str]) -> str:
    """
    Get file extension based on MIME type

    Args:
        mime_type: MIME type string

    Returns:
        File extension (defaults to .mp3)
    """
    if mime_type:
        for key, ext in MIME_TO_EXTENSION.items():
            if key in mime_type.lower():
                return ext
    return '.mp3'


def is_audio_file(filename: str) -> bool:
    """
    Check if a filename has an audio extension

    Args:
        filename: Name of the file

    Returns:
        True if audio file, False otherwise
    """
    return filename.lower().endswith(AUDIO_EXTENSIONS)


def open_folder(path: str) -> None:
    """
    Open a folder in the system file explorer

    Args:
        path: Path to the folder
    """
    os.makedirs(path, exist_ok=True)

    system = platform.system()

    if system == 'Windows':
        os.startfile(path)
    elif system == 'Darwin':  # macOS
        subprocess.run(['open', path])
    else:  # Linux
        subprocess.run(['xdg-open', path])


def format_channel_id(channel_id: str) -> int:
    """
    Format channel ID for Telegram API (add -100 prefix)

    Args:
        channel_id: Channel ID string

    Returns:
        Formatted channel ID as integer
    """
    return int(f"-100{channel_id}")


def generate_filename(post_id: int, mime_type: Optional[str] = None) -> str:
    """
    Generate a filename for a post

    Args:
        post_id: The post/message ID
        mime_type: Optional MIME type for extension

    Returns:
        Generated filename
    """
    ext = get_audio_extension(mime_type)
    return f"audio_{post_id}{ext}"