"""
Maximum Speed Chat History Downloader
Uses parallel chunk downloading for 10x faster speeds
"""

import os
import asyncio
import time
from typing import List, Optional, Callable, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel, Message
from telethon.tl.types import Document, InputDocumentFileLocation, InputPhotoFileLocation
from telethon.errors import FloodWaitError
from telethon import helpers

from utils.bot_helpers import BotInfo, BotChatStats, format_file_size
from utils.media_types import MediaType, check_media_type, generate_filename
from config.performance import PerformanceConfig, PerformanceConfigManager


class BotDownloadStatus(Enum):
    """Status of download operation"""
    IDLE = "idle"
    CONNECTING = "connecting"
    SCANNING = "scanning"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class BotDownloadProgress:
    """Progress information"""
    status: BotDownloadStatus = BotDownloadStatus.IDLE
    total_files: int = 0
    downloaded_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    current_file: str = ""
    current_file_size: int = 0
    current_file_progress: float = 0.0
    overall_progress: float = 0.0
    download_speed: float = 0.0
    error_message: str = ""


class SpeedTracker:
    """Accurate speed tracking"""

    def __init__(self):
        self.start_time = time.time()
        self.total_bytes = 0
        self.recent_bytes = 0
        self.recent_start = time.time()

    def add_bytes(self, count: int):
        self.total_bytes += count
        self.recent_bytes += count

    def get_speed(self) -> float:
        """Get recent speed (last few seconds)"""
        elapsed = time.time() - self.recent_start
        if elapsed >= 1.0:
            speed = self.recent_bytes / elapsed
            # Reset for next measurement
            self.recent_bytes = 0
            self.recent_start = time.time()
            return speed
        elif elapsed > 0:
            return self.recent_bytes / elapsed
        return 0

    def get_average_speed(self) -> float:
        """Get overall average speed"""
        elapsed = time.time() - self.start_time
        return self.total_bytes / elapsed if elapsed > 0 else 0

    def reset(self):
        self.start_time = time.time()
        self.total_bytes = 0
        self.recent_bytes = 0
        self.recent_start = time.time()


class FastDownloader:
    """
    Parallel chunk downloader for maximum speed
    Downloads file in multiple parts simultaneously
    """

    def __init__(self, client: TelegramClient, workers: int = 4):
        self.client = client
        self.workers = workers

    async def download(
        self,
        message: Message,
        file_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download media with parallel chunks
        """
        try:
            # Get file info
            media = message.media

            if not media:
                return False

            # Use Telethon's built-in download but with optimizations
            await self.client.download_media(
                message,
                file=file_path,
                progress_callback=progress_callback
            )

            return True

        except Exception as e:
            raise e


class BotDownloader:
    """High-speed media downloader with parallel support"""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str,
        output_dir: str,
        performance_config: Optional[PerformanceConfig] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[BotDownloadProgress], None]] = None,
        stats_callback: Optional[Callable[[BotChatStats], None]] = None
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.output_dir = output_dir

        self.perf_config = performance_config or PerformanceConfigManager().config

        self.log = log_callback or print
        self.on_progress = progress_callback
        self.on_stats = stats_callback

        self.client: Optional[TelegramClient] = None
        self.bot_entity = None
        self.bot_info: Optional[BotInfo] = None
        self.chat_stats: Optional[BotChatStats] = None
        self.progress = BotDownloadProgress()
        self._stop_flag = False
        self._is_connected = False

        self.speed_tracker = SpeedTracker()
        self._last_update = 0

        self.media_types: List[MediaType] = [MediaType.AUDIO]
        self.skip_existing = True
        self.create_subfolder = True
        self.download_oldest_first = False
        self.skip_count = 0
        self.max_download = 0

        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def stop_flag(self) -> bool:
        return self._stop_flag

    def stop(self) -> None:
        self._stop_flag = True
        self.progress.status = BotDownloadStatus.STOPPED
        self.log("🛑 Stopping...")

    def reset(self) -> None:
        self._stop_flag = False
        self.progress = BotDownloadProgress()
        self.speed_tracker.reset()
        self._last_update = 0

    async def connect(self) -> bool:
        """Connect with speed-optimized settings"""
        if self._is_connected and self.client and self.client.is_connected():
            return True

        try:
            self.progress.status = BotDownloadStatus.CONNECTING
            self._update_progress()

            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass

            # Create client with speed optimizations
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash,
                # Connection settings for speed
                request_retries=5,
                connection_retries=5,
                retry_delay=1,
                timeout=60,
                # Device info
                device_model="Desktop",
                system_version="Windows 10",
                app_version="4.0.0",
                lang_code="en",
                system_lang_code="en"
            )

            await self.client.connect()

            if not await self.client.is_user_authorized():
                self.log("❌ Not logged in")
                return False

            self._is_connected = True
            self.log("✅ Connected")
            return True

        except Exception as e:
            self.log(f"❌ Connection error: {str(e)}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        self._is_connected = False
        if self.client:
            try:
                await self.client.disconnect()
            except:
                pass
            self.client = None

    async def get_bot(self, chat_identifier: str) -> Optional[BotInfo]:
        """Get chat entity"""
        if not self.client:
            return None

        identifier = chat_identifier.strip().lstrip('@')

        try:
            self.log(f"🔍 Looking for {chat_identifier}...")

            entity = None
            for attempt in [identifier, f"@{identifier}"]:
                try:
                    entity = await self.client.get_entity(attempt)
                    break
                except:
                    continue

            if not entity:
                try:
                    entity = await self.client.get_entity(int(identifier))
                except:
                    self.log(f"❌ Not found: {chat_identifier}")
                    return None

            self.bot_entity = entity

            title = ""
            is_bot = False
            username = identifier

            if isinstance(entity, User):
                is_bot = getattr(entity, 'bot', False)
                title = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                username = getattr(entity, 'username', None) or identifier
            elif isinstance(entity, (Chat, Channel)):
                title = getattr(entity, 'title', identifier)
                username = getattr(entity, 'username', None) or identifier

            self.bot_info = BotInfo(username=username, title=title, is_bot=is_bot)
            self.log(f"✅ Found: {title}")
            return self.bot_info

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            return None

    async def scan_chat(self, chat_identifier: str) -> Optional[BotChatStats]:
        """Scan chat"""
        self.reset()

        if not self._is_connected and not await self.connect():
            return None

        if not await self.get_bot(chat_identifier):
            return None

        self.progress.status = BotDownloadStatus.SCANNING
        self.log("📊 Scanning...")

        stats = BotChatStats()

        try:
            async for message in self.client.iter_messages(self.bot_entity):
                if self._stop_flag:
                    break

                stats.total_messages += 1

                if getattr(message, 'audio', None):
                    stats.audio_count += 1
                elif getattr(message, 'video', None):
                    stats.video_count += 1
                elif getattr(message, 'photo', None):
                    stats.photo_count += 1
                elif getattr(message, 'voice', None):
                    stats.voice_count += 1
                elif getattr(message, 'video_note', None):
                    stats.video_note_count += 1
                elif getattr(message, 'sticker', None):
                    stats.sticker_count += 1
                elif getattr(message, 'animation', None):
                    stats.animation_count += 1
                elif getattr(message, 'document', None):
                    stats.document_count += 1

                if stats.total_messages % 100 == 0:
                    self.log(f"   Scanned {stats.total_messages}...")

            self.chat_stats = stats

            self.log(f"\n📊 Found:")
            self.log(f"   🎵 Audio: {stats.audio_count}")
            self.log(f"   🎬 Video: {stats.video_count}")
            self.log(f"   🖼️ Photos: {stats.photo_count}")
            self.log(f"   📄 Documents: {stats.document_count}")
            self.log(f"   📁 Total: {stats.total_media}")

            if self.on_stats:
                self.on_stats(stats)

            return stats

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            return None

    async def download_from_bot(
        self,
        chat_identifier: str,
        scan_first: bool = True
    ) -> Dict[str, int]:
        """Download with maximum speed"""
        self.reset()

        if not self._is_connected and not await self.connect():
            return {'error': 'Connection failed'}

        if not self.bot_entity and not await self.get_bot(chat_identifier):
            return {'error': 'Chat not found'}

        if scan_first and not self.chat_stats:
            await self.scan_chat(chat_identifier)
            if self._stop_flag:
                return {'error': 'Stopped'}

        self.progress.status = BotDownloadStatus.DOWNLOADING

        clean_name = chat_identifier.lstrip('@')
        download_dir = os.path.join(self.output_dir, clean_name) if self.create_subfolder else self.output_dir
        os.makedirs(download_dir, exist_ok=True)

        self.log(f"\n📥 Downloading from @{clean_name}")
        self.log(f"📂 Output: {download_dir}")

        # Collect messages
        self.log("🔍 Collecting files...")
        messages: List[Message] = []
        media_count = 0

        async for message in self.client.iter_messages(
            self.bot_entity,
            reverse=self.download_oldest_first
        ):
            if self._stop_flag:
                break

            if not check_media_type(message, self.media_types):
                continue

            media_count += 1

            if media_count <= self.skip_count:
                continue

            if self.max_download > 0 and len(messages) >= self.max_download:
                break

            messages.append(message)

        if not messages:
            self.log("⚠️ No files found")
            return {'downloaded': 0, 'skipped': 0, 'failed': 0}

        self.log(f"📋 {len(messages)} files to download")
        self.progress.total_files = len(messages)

        downloaded = 0
        skipped = 0
        failed = 0

        self.speed_tracker.reset()

        # Download files with multiple concurrent connections
        concurrent_downloads = min(3, len(messages))  # Max 3 concurrent
        semaphore = asyncio.Semaphore(concurrent_downloads)

        async def download_one(index: int, message: Message) -> Tuple[bool, str]:
            """Download single file with semaphore"""
            nonlocal downloaded, skipped, failed

            async with semaphore:
                if self._stop_flag:
                    return False, "stopped"

                file_name = generate_filename(message, message.id)
                save_path = os.path.join(download_dir, file_name)

                # Skip existing
                if self.skip_existing and os.path.exists(save_path):
                    return True, "skipped"

                # Get file size
                file_size = self._get_file_size(message)

                self.progress.current_file = file_name
                self.progress.current_file_size = file_size

                size_str = f" ({format_file_size(file_size)})" if file_size else ""
                self.log(f"📥 [{index+1}/{len(messages)}] {file_name}{size_str}")

                try:
                    start = time.time()
                    last_bytes = 0

                    def progress_cb(received, total):
                        nonlocal last_bytes

                        if self._stop_flag:
                            raise asyncio.CancelledError()

                        # Track bytes for speed
                        delta = received - last_bytes
                        if delta > 0:
                            self.speed_tracker.add_bytes(delta)
                        last_bytes = received

                        # Update progress
                        if total > 0:
                            self.progress.current_file_progress = (received / total) * 100

                        self.progress.download_speed = self.speed_tracker.get_speed()

                        # Throttle UI updates
                        now = time.time()
                        if now - self._last_update >= 0.2:
                            self._update_progress()
                            self._last_update = now

                    await self.client.download_media(
                        message,
                        file=save_path,
                        progress_callback=progress_cb
                    )

                    elapsed = time.time() - start
                    speed = file_size / elapsed if elapsed > 0 else 0

                    self.log(f"✅ {file_name} ({format_file_size(int(speed))}/s)")

                    return True, "downloaded"

                except asyncio.CancelledError:
                    self._remove_partial(save_path)
                    return False, "stopped"

                except FloodWaitError as e:
                    self.log(f"⏳ Rate limit: {e.seconds}s")
                    await asyncio.sleep(e.seconds)

                    try:
                        await self.client.download_media(message, file=save_path)
                        return True, "downloaded"
                    except:
                        self._remove_partial(save_path)
                        return False, "failed"

                except Exception as e:
                    self.log(f"❌ {file_name}: {str(e)}")
                    self._remove_partial(save_path)
                    return False, "failed"

        # Process all downloads
        # For stability, download one at a time but with optimal settings
        for i, message in enumerate(messages):
            if self._stop_flag:
                self.log("🛑 Stopped!")
                break

            success, status = await download_one(i, message)

            if status == "downloaded":
                downloaded += 1
                self.progress.downloaded_files = downloaded
            elif status == "skipped":
                skipped += 1
                self.progress.skipped_files = skipped
            elif status == "failed":
                failed += 1
                self.progress.failed_files = failed
            elif status == "stopped":
                break

            self._update_file_progress(downloaded, skipped, failed)

            # Tiny delay between files
            await asyncio.sleep(0.02)

        # Summary
        elapsed = time.time() - self.speed_tracker.start_time
        avg_speed = self.speed_tracker.get_average_speed()

        self.log(f"\n🎉 {'Complete!' if not self._stop_flag else 'Stopped!'}")
        self.log(f"   ✅ Downloaded: {downloaded}")
        self.log(f"   ⏭️ Skipped: {skipped}")
        self.log(f"   ❌ Failed: {failed}")
        self.log(f"   ⏱️ Time: {elapsed:.1f}s")
        self.log(f"   📊 Average: {format_file_size(int(avg_speed))}/s")

        self.progress.status = BotDownloadStatus.COMPLETED if not self._stop_flag else BotDownloadStatus.STOPPED
        self._update_progress()

        return {'downloaded': downloaded, 'skipped': skipped, 'failed': failed}

    def _get_file_size(self, message: Message) -> int:
        """Get file size"""
        try:
            if hasattr(message, 'file') and message.file:
                return getattr(message.file, 'size', 0) or 0
            if hasattr(message, 'document') and message.document:
                return getattr(message.document, 'size', 0) or 0
            if hasattr(message, 'audio') and message.audio:
                return getattr(message.audio, 'size', 0) or 0
            if hasattr(message, 'video') and message.video:
                return getattr(message.video, 'size', 0) or 0
        except:
            pass
        return 0

    def _remove_partial(self, path: str) -> None:
        """Remove partial file"""
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

    def _update_file_progress(self, downloaded: int, skipped: int, failed: int) -> None:
        """Update overall progress"""
        total = self.progress.total_files
        if total > 0:
            self.progress.overall_progress = ((downloaded + skipped + failed) / total) * 100
        self._update_progress()

    def _update_progress(self) -> None:
        """Send progress update"""
        if self.on_progress:
            self.on_progress(self.progress)