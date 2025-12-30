"""
Media type definitions and utilities
"""

from enum import Enum
from typing import List, Tuple, Dict


class MediaType(Enum):
    """Supported media types for download"""
    AUDIO = "audio"
    VIDEO = "video"
    PHOTO = "photo"
    DOCUMENT = "document"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    ANIMATION = "animation"
    STICKER = "sticker"


# Media type display information
MEDIA_TYPE_INFO: Dict[MediaType, Dict] = {
    MediaType.AUDIO: {
        'label': 'Audio',
        'extensions': '.mp3, .m4a, .wav, .ogg, .flac, .aac',
        'icon': '🎵',
        'description': 'Music and audio files'
    },
    MediaType.VIDEO: {
        'label': 'Video',
        'extensions': '.mp4, .mkv, .avi, .mov, .webm',
        'icon': '🎬',
        'description': 'Video files'
    },
    MediaType.PHOTO: {
        'label': 'Photo',
        'extensions': '.jpg, .png, .webp, .gif',
        'icon': '🖼️',
        'description': 'Images and photos'
    },
    MediaType.DOCUMENT: {
        'label': 'Document',
        'extensions': '.pdf, .doc, .docx, .xls, .zip, etc.',
        'icon': '📄',
        'description': 'Documents and files'
    },
    MediaType.VOICE: {
        'label': 'Voice Message',
        'extensions': '.ogg, .opus',
        'icon': '🎤',
        'description': 'Voice recordings'
    },
    MediaType.VIDEO_NOTE: {
        'label': 'Video Note',
        'extensions': '.mp4 (circular)',
        'icon': '⭕',
        'description': 'Round video messages'
    },
    MediaType.ANIMATION: {
        'label': 'Animation/GIF',
        'extensions': '.gif, .mp4',
        'icon': '🎞️',
        'description': 'Animated images and GIFs'
    },
    MediaType.STICKER: {
        'label': 'Sticker',
        'extensions': '.webp, .tgs, .webm',
        'icon': '😀',
        'description': 'Telegram stickers'
    }
}

# Extension mappings for each media type
MEDIA_EXTENSIONS: Dict[MediaType, Tuple[str, ...]] = {
    MediaType.AUDIO: (
        '.mp3', '.m4a', '.wav', '.ogg', '.flac',
        '.aac', '.wma', '.opus', '.aiff'
    ),
    MediaType.VIDEO: (
        '.mp4', '.mkv', '.avi', '.mov', '.webm',
        '.flv', '.wmv', '.m4v', '.3gp'
    ),
    MediaType.PHOTO: (
        '.jpg', '.jpeg', '.png', '.webp', '.gif',
        '.bmp', '.tiff', '.heic'
    ),
    MediaType.DOCUMENT: (
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.ppt', '.pptx', '.txt', '.zip', '.rar',
        '.7z', '.tar', '.gz', '.epub', '.mobi'
    ),
    MediaType.VOICE: (
        '.ogg', '.opus', '.oga'
    ),
    MediaType.VIDEO_NOTE: (
        '.mp4',
    ),
    MediaType.ANIMATION: (
        '.gif', '.mp4'
    ),
    MediaType.STICKER: (
        '.webp', '.tgs', '.webm'
    )
}


def get_media_type_label(media_type: MediaType) -> str:
    """Get display label for media type"""
    info = MEDIA_TYPE_INFO.get(media_type, {})
    icon = info.get('icon', '')
    label = info.get('label', media_type.value)
    extensions = info.get('extensions', '')
    return f"{icon} {label} ({extensions})"


def get_media_type_short_label(media_type: MediaType) -> str:
    """Get short display label for media type"""
    info = MEDIA_TYPE_INFO.get(media_type, {})
    icon = info.get('icon', '')
    label = info.get('label', media_type.value)
    return f"{icon} {label}"


def get_all_media_types() -> List[MediaType]:
    """Get list of all media types"""
    return list(MediaType)


def check_media_type(message, selected_types: List[MediaType]) -> bool:
    """
    Check if a message matches any of the selected media types

    Args:
        message: Telegram message object
        selected_types: List of selected MediaType enums

    Returns:
        True if message matches any selected type
    """
    if not selected_types:
        return False

    for media_type in selected_types:
        if media_type == MediaType.AUDIO and message.audio:
            return True
        elif media_type == MediaType.VIDEO and message.video:
            return True
        elif media_type == MediaType.PHOTO and message.photo:
            return True
        elif media_type == MediaType.DOCUMENT and message.document:
            # Exclude other specific types that are also documents
            if not (message.audio or message.video or message.voice or
                    message.video_note or message.sticker):
                return True
        elif media_type == MediaType.VOICE and message.voice:
            return True
        elif media_type == MediaType.VIDEO_NOTE and message.video_note:
            return True
        elif media_type == MediaType.ANIMATION and message.animation:
            return True
        elif media_type == MediaType.STICKER and message.sticker:
            return True

    return False


def get_file_extension(message) -> str:
    """
    Get appropriate file extension for a message

    Args:
        message: Telegram message object

    Returns:
        File extension string
    """
    # Try to get from file name
    if message.file and message.file.name:
        name = message.file.name
        if '.' in name:
            return '.' + name.split('.')[-1].lower()

    # Try to get from mime type
    if message.file and message.file.mime_type:
        mime = message.file.mime_type.lower()

        # Audio
        if 'audio/mpeg' in mime or 'audio/mp3' in mime:
            return '.mp3'
        elif 'audio/mp4' in mime or 'audio/m4a' in mime:
            return '.m4a'
        elif 'audio/ogg' in mime:
            return '.ogg'
        elif 'audio/wav' in mime:
            return '.wav'
        elif 'audio/flac' in mime:
            return '.flac'

        # Video
        elif 'video/mp4' in mime:
            return '.mp4'
        elif 'video/webm' in mime:
            return '.webm'
        elif 'video/x-matroska' in mime:
            return '.mkv'
        elif 'video/quicktime' in mime:
            return '.mov'

        # Image
        elif 'image/jpeg' in mime:
            return '.jpg'
        elif 'image/png' in mime:
            return '.png'
        elif 'image/webp' in mime:
            return '.webp'
        elif 'image/gif' in mime:
            return '.gif'

        # Documents
        elif 'application/pdf' in mime:
            return '.pdf'
        elif 'application/zip' in mime:
            return '.zip'

    # Default based on message type
    if message.audio:
        return '.mp3'
    elif message.video:
        return '.mp4'
    elif message.photo:
        return '.jpg'
    elif message.voice:
        return '.ogg'
    elif message.video_note:
        return '.mp4'
    elif message.sticker:
        return '.webp'
    elif message.animation:
        return '.gif'

    return '.bin'


def generate_filename(message, post_id: int) -> str:
    """
    Generate a filename for a message

    Args:
        message: Telegram message object
        post_id: Post/message ID

    Returns:
        Generated filename
    """
    # Try to use original filename
    if message.file and message.file.name:
        return message.file.name

    # Generate based on type
    ext = get_file_extension(message)

    if message.audio:
        prefix = "audio"
    elif message.video:
        prefix = "video"
    elif message.photo:
        prefix = "photo"
    elif message.voice:
        prefix = "voice"
    elif message.video_note:
        prefix = "video_note"
    elif message.sticker:
        prefix = "sticker"
    elif message.animation:
        prefix = "animation"
    elif message.document:
        prefix = "document"
    else:
        prefix = "file"

    return f"{prefix}_{post_id}{ext}"