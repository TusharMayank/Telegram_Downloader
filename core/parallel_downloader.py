"""
Parallel/Concurrent download manager for improved speed
"""

import os
import asyncio
import time
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from config.performance import PerformanceConfig, PerformanceConfigManager
from utils.helpers import format_channel_id
from utils.media_types import MediaType, check_media_type, generate_filename


class DownloadStatus(Enum):
    """Status of a download task"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DownloadTask:
    """Represents a single download task"""
    post_id: int
    status: DownloadStatus = DownloadStatus.PENDING
    file_name: Optional[str] = None
    file_size: int = 0
    downloaded_size: int = 0
    error_message: Optional[str] = None
    retries: int = 0


@dataclass
class DownloadProgress:
    """Progress information for downloads"""
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    current_file: str = ""
    current_file_progress: float = 0.0
    overall_progress: float = 0.0
    download_speed: float = 0.0  # bytes per second
    eta_seconds: float = 0.0


class ParallelDownloader:
    """
    High-performance parallel downloader for Telegram Media Downloader
    Supports all media types with concurrent download capability
    """

    def __init__(
            self,
            api_id: int,
            api_hash: str,
            session_name: str,
            channel_id: str,
            output_dir: str,
            performance_config: Optional[PerformanceConfig] = None,
            log_callback: Optional[Callable[[str], None]] = None,
            progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
            status_callback: Optional[Callable[[str], None]] = None,
            file_progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.channel_id = channel_id
        self.output_dir = output_dir
        self.full_channel_id = format_channel_id(channel_id)

        # Performance config
        if performance_config is None:
            self.perf_config = PerformanceConfigManager().config
        else:
            self.perf_config = performance_config

        # Callbacks
        self.log = log_callback or print
        self.on_progress = progress_callback
        self.on_status = status_callback or (lambda x: None)
        self.on_file_progress = file_progress_callback

        # Options
        self.media_types: List[MediaType] = [MediaType.AUDIO]
        self.skip_existing = True
        self.stop_flag = False

        # State
        self.client: Optional[TelegramClient] = None
        self.channel = None
        self.tasks: List[DownloadTask] = []
        self.progress = DownloadProgress()
        self.semaphore: Optional[asyncio.Semaphore] = None

        # Speed tracking
        self._speed_samples: List[float] = []
        self._last_speed_update = 0.0
        self._bytes_since_last_update = 0

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def stop(self) -> None:
        """Signal to stop downloading"""
        self.stop_flag = True
        self.log("🛑 Stop signal received...")

    def reset(self) -> None:
        """Reset state for new download session"""
        self.stop_flag = False
        self.tasks = []
        self.progress = DownloadProgress()
        self._speed_samples = []
        self._last_speed_update = time.time()
        self._bytes_since_last_update = 0

    async def _create_client(self) -> TelegramClient:
        """Create and configure the Telegram client"""
        client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash,
            request_retries=self.perf_config.connection_retries,
            connection_retries=self.perf_config.connection_retries,
            retry_delay=self.perf_config.retry_delay,
            timeout=self.perf_config.request_timeout,
            use_ipv6=self.perf_config.use_ipv6
        )

        await client.connect()

        if not await client.is_user_authorized():
            raise Exception("Client not authorized. Please login first.")

        return client

    async def _get_channel(self, client: TelegramClient):
        """Get the channel entity"""
        try:
            channel = await client.get_entity(self.full_channel_id)
            return channel
        except Exception as e:
            raise Exception(f"Failed to get channel: {str(e)}")

    def _update_progress(self) -> None:
        """Update and broadcast progress"""
        completed = sum(1 for t in self.tasks if t.status == DownloadStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == DownloadStatus.FAILED)
        skipped = sum(1 for t in self.tasks if t.status == DownloadStatus.SKIPPED)

        self.progress.completed_files = completed
        self.progress.failed_files = failed
        self.progress.skipped_files = skipped

        total = self.progress.total_files
        if total > 0:
            self.progress.overall_progress = ((completed + failed + skipped) / total) * 100

        # Calculate speed
        now = time.time()
        elapsed = now - self._last_speed_update

        if elapsed >= self.perf_config.progress_update_interval:
            if elapsed > 0:
                speed = self._bytes_since_last_update / elapsed
                self._speed_samples.append(speed)

                # Keep last 10 samples for average
                if len(self._speed_samples) > 10:
                    self._speed_samples.pop(0)

                self.progress.download_speed = sum(self._speed_samples) / len(self._speed_samples)

            self._last_speed_update = now
            self._bytes_since_last_update = 0

        if self.on_progress:
            self.on_progress(self.progress)

    async def _download_file_with_progress(
            self,
            message,
            save_path: str,
            task: DownloadTask
    ) -> bool:
        """Download a file with progress tracking"""

        try:
            # Get file size if available
            if message.file:
                task.file_size = message.file.size or 0

            # Progress callback for this file
            def progress_callback(received, total):
                task.downloaded_size = received
                task.file_size = total

                self._bytes_since_last_update += received - getattr(self, '_last_received', 0)
                self._last_received = received

                if total > 0:
                    file_progress = (received / total) * 100
                    self.progress.current_file_progress = file_progress

                    if self.on_file_progress:
                        self.on_file_progress(task.file_name, file_progress)

                self._update_progress()

            self._last_received = 0

            # Download with progress
            await message.download_media(
                file=save_path,
                progress_callback=progress_callback
            )

            return True

        except Exception as e:
            raise e

    async def _download_single_task(
            self,
            client: TelegramClient,
            channel,
            task: DownloadTask
    ) -> None:
        """Download a single file (used in parallel downloads)"""

        async with self.semaphore:
            if self.stop_flag:
                return

            task.status = DownloadStatus.DOWNLOADING
            self.progress.current_file = f"Post #{task.post_id}"
            self._update_progress()

            try:
                # Get message
                message = await client.get_messages(channel, ids=task.post_id)

                if message is None:
                    task.status = DownloadStatus.SKIPPED
                    task.error_message = "Not found"
                    self.log(f"⚠️ Post #{task.post_id}: Not found")
                    return

                # Check media type
                if not check_media_type(message, self.media_types):
                    task.status = DownloadStatus.SKIPPED
                    task.error_message = "Media type not selected"
                    self.log(f"⏭️ Post #{task.post_id}: Skipped (type not selected)")
                    return

                # Generate filename
                file_name = generate_filename(message, task.post_id)
                task.file_name = file_name
                save_path = os.path.join(self.output_dir, file_name)

                # Check existing
                if self.skip_existing and os.path.exists(save_path):
                    task.status = DownloadStatus.SKIPPED
                    task.error_message = "Already exists"
                    self.log(f"⏭️ Post #{task.post_id}: {file_name} (exists)")
                    return

                self.progress.current_file = file_name
                self.log(f"📥 Downloading: {file_name}")

                # Download
                success = await self._download_file_with_progress(
                    message, save_path, task
                )

                if success:
                    task.status = DownloadStatus.COMPLETED
                    self.log(f"✅ Completed: {file_name}")

            except FloodWaitError as e:
                if self.perf_config.auto_handle_flood_wait:
                    self.log(f"⏳ Rate limited. Waiting {e.seconds}s...")
                    await asyncio.sleep(e.seconds)

                    # Retry
                    task.retries += 1
                    if task.retries <= self.perf_config.max_retries_per_file:
                        await self._download_single_task(client, channel, task)
                    else:
                        task.status = DownloadStatus.FAILED
                        task.error_message = f"Max retries exceeded"
                else:
                    task.status = DownloadStatus.FAILED
                    task.error_message = f"FloodWait: {e.seconds}s"

            except Exception as e:
                task.retries += 1

                if task.retries <= self.perf_config.max_retries_per_file:
                    self.log(f"⚠️ Retry {task.retries}/{self.perf_config.max_retries_per_file}: {task.post_id}")
                    await asyncio.sleep(self.perf_config.retry_delay)
                    await self._download_single_task(client, channel, task)
                else:
                    task.status = DownloadStatus.FAILED
                    task.error_message = str(e)
                    self.log(f"❌ Failed: Post #{task.post_id} - {str(e)}")

            finally:
                self._update_progress()

                # Delay between files
                if self.perf_config.delay_between_files > 0:
                    await asyncio.sleep(self.perf_config.delay_between_files)

    async def download_posts(self, post_ids: List[int]) -> Dict[str, int]:
        """
        Download multiple posts with parallel/concurrent downloads

        Args:
            post_ids: List of post IDs to download

        Returns:
            Dictionary with download statistics
        """
        self.reset()

        # Create tasks
        self.tasks = [DownloadTask(post_id=pid) for pid in post_ids]
        self.progress.total_files = len(self.tasks)

        self.log(f"📋 Preparing to download {len(post_ids)} posts")
        self.log(f"⚡ Parallel downloads: {self.perf_config.max_concurrent_downloads}")
        self.log(f"📦 Chunk size: {self.perf_config.download_chunk_size} KB")

        # Create semaphore for limiting concurrent downloads
        if self.perf_config.enabled_parallel:
            self.semaphore = asyncio.Semaphore(
                self.perf_config.max_concurrent_downloads
            )
        else:
            self.semaphore = asyncio.Semaphore(1)

        self.on_status("Connecting...")

        try:
            # Create and connect client
            self.client = await self._create_client()
            self.log("✅ Connected to Telegram")

            # Get channel
            self.channel = await self._get_channel(self.client)
            channel_title = getattr(self.channel, 'title', 'Private Channel')
            self.log(f"📢 Channel: {channel_title}")

            self.on_status("Downloading...")

            # Process in batches
            batch_size = self.perf_config.batch_size

            for batch_start in range(0, len(self.tasks), batch_size):
                if self.stop_flag:
                    break

                batch_end = min(batch_start + batch_size, len(self.tasks))
                batch_tasks = self.tasks[batch_start:batch_end]

                batch_num = (batch_start // batch_size) + 1
                total_batches = (len(self.tasks) + batch_size - 1) // batch_size
                self.log(f"📦 Processing batch {batch_num}/{total_batches}")

                # Create download coroutines
                download_coros = [
                    self._download_single_task(self.client, self.channel, task)
                    for task in batch_tasks
                ]

                # Run batch concurrently
                await asyncio.gather(*download_coros, return_exceptions=True)

                # Delay between batches
                if batch_end < len(self.tasks) and self.perf_config.delay_between_batches > 0:
                    self.log(f"⏸️ Batch delay: {self.perf_config.delay_between_batches}s")
                    await asyncio.sleep(self.perf_config.delay_between_batches)

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")

        finally:
            # Disconnect
            if self.client:
                await self.client.disconnect()

        # Final statistics
        stats = {
            'total': len(self.tasks),
            'completed': sum(1 for t in self.tasks if t.status == DownloadStatus.COMPLETED),
            'failed': sum(1 for t in self.tasks if t.status == DownloadStatus.FAILED),
            'skipped': sum(1 for t in self.tasks if t.status == DownloadStatus.SKIPPED)
        }

        self.log(f"\n🎉 Download complete!")
        self.log(f"   ✅ Completed: {stats['completed']}")
        self.log(f"   ❌ Failed: {stats['failed']}")
        self.log(f"   ⏭️ Skipped: {stats['skipped']}")

        self.on_status(f"Done: {stats['completed']}/{stats['total']} downloaded")

        return stats

    async def download_sequential(
            self,
            skip_count: int,
            max_download: int,
            reverse: bool = False
    ) -> Dict[str, int]:
        """
        Download files sequentially from channel with skip

        Args:
            skip_count: Number of matching files to skip
            max_download: Maximum files to download
            reverse: Download oldest first

        Returns:
            Dictionary with download statistics
        """
        self.reset()

        self.log(f"📋 Sequential download: skip {skip_count}, max {max_download}")
        self.log(f"⚡ Parallel downloads: {self.perf_config.max_concurrent_downloads}")

        self.progress.total_files = max_download

        if self.perf_config.enabled_parallel:
            self.semaphore = asyncio.Semaphore(
                self.perf_config.max_concurrent_downloads
            )
        else:
            self.semaphore = asyncio.Semaphore(1)

        self.on_status("Connecting...")

        post_ids = []
        media_count = 0

        try:
            self.client = await self._create_client()
            self.log("✅ Connected to Telegram")

            self.channel = await self._get_channel(self.client)
            channel_title = getattr(self.channel, 'title', 'Private Channel')
            self.log(f"📢 Channel: {channel_title}")

            self.on_status("Scanning channel...")
            self.log("🔍 Scanning for matching media...")

            # Collect post IDs first
            async for message in self.client.iter_messages(self.channel, reverse=reverse):
                if self.stop_flag:
                    break

                if len(post_ids) >= max_download:
                    break

                if not check_media_type(message, self.media_types):
                    continue

                media_count += 1

                if media_count <= skip_count:
                    continue

                post_ids.append(message.id)

            self.log(f"📋 Found {len(post_ids)} files to download")

            # Now download collected posts
            if post_ids:
                # Disconnect and reconnect for clean state
                await self.client.disconnect()
                self.client = None

                # Use the parallel download method
                return await self.download_posts(post_ids)

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")

        finally:
            if self.client:
                await self.client.disconnect()

        return {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }