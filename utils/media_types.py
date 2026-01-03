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
        if media_type == MediaType.AUDIO and getattr(message, 'audio', None):
            return True
        elif media_type == MediaType.VIDEO and getattr(message, 'video', None):
            return True
        elif media_type == MediaType.PHOTO and getattr(message, 'photo', None):
            return True
        elif media_type == MediaType.DOCUMENT and getattr(message, 'document', None):
            # Exclude other specific types that are also documents
            if not (getattr(message, 'audio', None) or
                    getattr(message, 'video', None) or
                    getattr(message, 'voice', None) or
                    getattr(message, 'video_note', None) or
                    getattr(message, 'sticker', None)):
                return True
        elif media_type == MediaType.VOICE and getattr(message, 'voice', None):
            return True
        elif media_type == MediaType.VIDEO_NOTE and getattr(message, 'video_note', None):
            return True
        elif media_type == MediaType.ANIMATION and (
                getattr(message, 'animation', None) or getattr(message, 'gif', None)):
            return True
        elif media_type == MediaType.STICKER and getattr(message, 'sticker', None):
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
    if getattr(message, 'file', None) and getattr(message.file, 'name', None):
        name = message.file.name
        if '.' in name:
            return '.' + name.split('.')[-1].lower()

    # Try to get from mime type
    if getattr(message, 'file', None) and getattr(message.file, 'mime_type', None):
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
    if getattr(message, 'audio', None):
        return '.mp3'
    elif getattr(message, 'video', None):
        return '.mp4'
    elif getattr(message, 'photo', None):
        return '.jpg'
    elif getattr(message, 'voice', None):
        return '.ogg'
    elif getattr(message, 'video_note', None):
        return '.mp4'
    elif getattr(message, 'sticker', None):
        return '.webp'
    elif getattr(message, 'animation', None) or getattr(message, 'gif', None):
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
    if getattr(message, 'file', None) and getattr(message.file, 'name', None):
        return message.file.name

    # Generate based on type
    ext = get_file_extension(message)

    if getattr(message, 'audio', None):
        prefix = "audio"
    elif getattr(message, 'video', None):
        prefix = "video"
    elif getattr(message, 'photo', None):
        prefix = "photo"
    elif getattr(message, 'voice', None):
        prefix = "voice"
    elif getattr(message, 'video_note', None):
        prefix = "video_note"
    elif getattr(message, 'sticker', None):
        prefix = "sticker"
    elif getattr(message, 'animation', None) or getattr(message, 'gif', None):
        prefix = "animation"
    elif getattr(message, 'document', None):
        prefix = "document"
    else:
        prefix = "file"

    return f"{prefix}_{post_id}{ext}"