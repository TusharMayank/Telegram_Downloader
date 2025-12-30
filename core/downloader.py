"""
Media download logic - supports all media types
"""

import os
import asyncio
from typing import List, Optional, Callable
from telethon.errors import FloodWaitError

from .client import TelegramClientWrapper
from utils.helpers import format_channel_id
from utils.media_types import (
    MediaType,
    check_media_type,
    generate_filename
)


class AudioDownloader:
    """
    Handles downloading media files from Telegram
    Note: Class name kept as AudioDownloader for backwards compatibility
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str,
        channel_id: str,
        output_dir: str,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.channel_id = channel_id
        self.output_dir = output_dir
        self.full_channel_id = format_channel_id(channel_id)

        # Callbacks
        self.log = log_callback or print
        self.update_progress = progress_callback or (lambda x: None)
        self.update_status = status_callback or (lambda x: None)

        # Options
        self.media_types: List[MediaType] = [MediaType.AUDIO]  # Default
        self.skip_existing = True
        self.stop_flag = False

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    # Legacy property for backwards compatibility
    @property
    def audio_only(self) -> bool:
        return self.media_types == [MediaType.AUDIO]

    @audio_only.setter
    def audio_only(self, value: bool):
        if value:
            self.media_types = [MediaType.AUDIO]

    def stop(self) -> None:
        """Signal to stop downloading"""
        self.stop_flag = True

    def reset(self) -> None:
        """Reset the stop flag"""
        self.stop_flag = False

    def _get_media_type_names(self) -> str:
        """Get comma-separated list of selected media type names"""
        return ", ".join([t.value for t in self.media_types])

    async def download_posts(self, post_ids: List[int]) -> int:
        """
        Download specific posts by ID

        Args:
            post_ids: List of post IDs to download

        Returns:
            Number of files downloaded
        """
        self.reset()
        downloaded = 0
        total = len(post_ids)

        self.log(f"Connecting to Telegram (Session: {self.session_name})...")
        self.log(f"📋 Media types: {self._get_media_type_names()}")
        self.update_status("Connecting...")

        client_wrapper = TelegramClientWrapper(
            self.api_id,
            self.api_hash,
            self.session_name
        )

        client = await client_wrapper.connect()

        try:
            self.log("✅ Connected to Telegram")

            # Get channel
            try:
                channel = await client.get_entity(self.full_channel_id)
                channel_title = getattr(channel, 'title', 'Private Channel')
                self.log(f"📢 Found channel: {channel_title}")
            except Exception as e:
                self.log(f"❌ Failed to get channel: {str(e)}")
                self.log("Make sure you are a member of this channel")
                return 0

            # Download each post
            for idx, post_id in enumerate(post_ids, 1):
                if self.stop_flag:
                    self.log("🛑 Download stopped by user")
                    break

                progress = (idx / total) * 100
                self.update_progress(progress)
                self.update_status(f"Processing post {post_id} ({idx}/{total})")

                result = await self._download_single_post(client, channel, post_id)
                if result:
                    downloaded += 1

            self.log(f"\n🎉 Download complete! Downloaded {downloaded}/{total} files")
            self.update_status(f"Complete: {downloaded}/{total} files downloaded")
            self.update_progress(100)

        finally:
            await client_wrapper.disconnect()

        return downloaded

    async def download_sequential(
        self,
        skip_count: int,
        max_download: int,
        reverse: bool = False
    ) -> int:
        """
        Download files sequentially with skip option

        Args:
            skip_count: Number of matching files to skip
            max_download: Maximum files to download
            reverse: Whether to download oldest first

        Returns:
            Number of files downloaded
        """
        self.reset()
        media_count = 0
        downloaded = 0

        self.log(f"Connecting to Telegram (Session: {self.session_name})...")
        self.log(f"📋 Media types: {self._get_media_type_names()}")

        client_wrapper = TelegramClientWrapper(
            self.api_id,
            self.api_hash,
            self.session_name
        )

        client = await client_wrapper.connect()

        try:
            self.log("✅ Connected to Telegram")

            # Get channel
            try:
                channel = await client.get_entity(self.full_channel_id)
                channel_title = getattr(channel, 'title', 'Private Channel')
                self.log(f"📢 Found channel: {channel_title}")
            except Exception as e:
                self.log(f"❌ Failed to get channel: {str(e)}")
                return 0

            self.log(f"Scanning channel (skip first {skip_count}, download max {max_download})...")

            async for message in client.iter_messages(channel, reverse=reverse):
                if self.stop_flag:
                    self.log("🛑 Download stopped by user")
                    break

                if downloaded >= max_download:
                    break

                # Check if message matches selected media types
                if not check_media_type(message, self.media_types):
                    continue

                media_count += 1

                # Skip if needed
                if media_count <= skip_count:
                    file_name = generate_filename(message, message.id)
                    self.log(f"⏭️ Skipping #{media_count}: {file_name}")
                    continue

                # Generate filename
                file_name = generate_filename(message, message.id)
                save_path = os.path.join(self.output_dir, file_name)

                # Skip existing
                if self.skip_existing and os.path.exists(save_path):
                    self.log(f"⏭️ Already exists: {file_name}")
                    continue

                # Download
                self.log(f"📥 Downloading #{media_count}: {file_name}")

                try:
                    await message.download_media(file=save_path)
                    self.log(f"✅ Downloaded: {file_name}")
                    downloaded += 1

                    progress = (downloaded / max_download) * 100
                    self.update_progress(progress)
                    self.update_status(f"Downloaded {downloaded}/{max_download}")

                except Exception as e:
                    self.log(f"❌ Error downloading {file_name}: {str(e)}")

            self.log(f"\n🎉 Done! Downloaded {downloaded} files after skipping {skip_count}")

        finally:
            await client_wrapper.disconnect()

        return downloaded

    async def _download_single_post(self, client, channel, post_id: int) -> bool:
        """Download a single post"""
        try:
            message = await client.get_messages(channel, ids=post_id)

            if message is None:
                self.log(f"⚠️ Post #{post_id}: Not found or no access")
                return False

            # Check if message matches selected media types
            if not check_media_type(message, self.media_types):
                # Check if it's a text message
                if message.text and not message.media:
                    self.log(f"⏭️ Post #{post_id}: Text message (skipped)")
                else:
                    self.log(f"⏭️ Post #{post_id}: Media type not selected")
                return False

            # Generate filename
            file_name = generate_filename(message, post_id)
            save_path = os.path.join(self.output_dir, file_name)

            # Skip existing
            if self.skip_existing and os.path.exists(save_path):
                self.log(f"⏭️ Post #{post_id}: Already exists ({file_name})")
                return False

            self.log(f"📥 Downloading: {file_name}")

            await message.download_media(file=save_path)

            self.log(f"✅ Downloaded: {file_name}")
            return True

        except FloodWaitError as e:
            self.log(f"⏳ Rate limited. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self._download_single_post(client, channel, post_id)
        except Exception as e:
            self.log(f"❌ Post #{post_id}: Error - {str(e)}")
            return False