"""
Bot-related helper utilities
"""

import re
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class BotInfo:
    """Information about a Telegram bot"""
    username: str
    title: str = ""
    is_bot: bool = True
    can_read_history: bool = True


@dataclass
class BotChatStats:
    """Statistics about media in bot chat"""
    total_messages: int = 0
    audio_count: int = 0
    video_count: int = 0
    photo_count: int = 0
    document_count: int = 0
    voice_count: int = 0
    video_note_count: int = 0
    animation_count: int = 0
    sticker_count: int = 0

    @property
    def total_media(self) -> int:
        return (
                self.audio_count +
                self.video_count +
                self.photo_count +
                self.document_count +
                self.voice_count +
                self.video_note_count +
                self.animation_count +
                self.sticker_count
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            'total_messages': self.total_messages,
            'audio': self.audio_count,
            'video': self.video_count,
            'photo': self.photo_count,
            'document': self.document_count,
            'voice': self.voice_count,
            'video_note': self.video_note_count,
            'animation': self.animation_count,
            'sticker': self.sticker_count,
            'total_media': self.total_media
        }


def parse_bot_username(input_text: str) -> Optional[str]:
    """
    Parse and clean bot username from various input formats

    Args:
        input_text: User input (username, @username, or URL)

    Returns:
        Clean bot username without @ or None if invalid

    Examples:
        "MyBot" -> "MyBot"
        "@MyBot" -> "MyBot"
        "https://t.me/MyBot" -> "MyBot"
        "t.me/MyBot?start=abc" -> "MyBot"
    """
    if not input_text:
        return None

    text = input_text.strip()

    # Remove @ prefix
    if text.startswith('@'):
        text = text[1:]

    # Handle URLs
    url_patterns = [
        r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)',
        r'(?:https?://)?telegram\.me/([a-zA-Z0-9_]+)',
    ]

    for pattern in url_patterns:
        match = re.search(pattern, text)
        if match:
            text = match.group(1)
            break

    # Remove any query parameters
    if '?' in text:
        text = text.split('?')[0]

    # Validate username format
    if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', text):
        return text

    # Check for bot suffix (common pattern)
    if text.lower().endswith('bot'):
        return text

    return text if text else None


def parse_bot_link(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse bot link to extract username and start parameter

    Args:
        url: Bot URL like https://t.me/BotName?start=CODE

    Returns:
        Tuple of (bot_username, start_parameter) or (None, None)
    """
    if not url:
        return None, None

    # Pattern for t.me links with start parameter
    pattern = r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)\?start=([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)

    if match:
        return match.group(1), match.group(2)

    # Just username without start parameter
    username = parse_bot_username(url)
    return username, None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "4.2 MB"
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_duration(seconds: int) -> str:
    """
    Format duration in human readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "3:45" or "1:23:45"
    """
    if seconds < 0:
        return "0:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"