"""
Telegram client wrapper for handling connections
"""

import asyncio
import glob
from typing import Optional, Dict, List, Callable
from telethon import TelegramClient


class TelegramClientWrapper:
    """Wrapper class for Telegram client operations"""

    def __init__(self, api_id: int, api_hash: str, session_name: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> TelegramClient:
        """Create and connect the Telegram client"""
        self.client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash
        )
        await self.client.connect()
        return self.client

    async def disconnect(self) -> None:
        """Disconnect the client"""
        if self.client:
            await self.client.disconnect()
            self.client = None

    async def is_authorized(self) -> bool:
        """Check if the client is authorized"""
        if self.client:
            return await self.client.is_user_authorized()
        return False

    async def get_me(self):
        """Get current user info"""
        if self.client:
            return await self.client.get_me()
        return None

    async def get_entity(self, entity_id: int):
        """Get an entity by ID"""
        if self.client:
            return await self.client.get_entity(entity_id)
        return None

    async def get_messages(self, channel, ids):
        """Get specific messages by IDs"""
        if self.client:
            return await self.client.get_messages(channel, ids=ids)
        return None

    async def iter_messages(self, channel, reverse: bool = False):
        """Iterate through channel messages"""
        if self.client:
            async for message in self.client.iter_messages(channel, reverse=reverse):
                yield message

    async def start(self) -> None:
        """Start the client (interactive login)"""
        if self.client:
            await self.client.start()

    @staticmethod
    def detect_sessions() -> List[str]:
        """Detect all .session files in current directory"""
        session_files = glob.glob("*.session")
        return [sf.replace('.session', '') for sf in session_files]

    @staticmethod
    async def get_session_info(
            api_id: int,
            api_hash: str,
            session_name: str
    ) -> Dict[str, str]:
        """Get account info for a session"""
        try:
            client = TelegramClient(session_name, api_id, api_hash)
            await client.connect()

            if await client.is_user_authorized():
                me = await client.get_me()
                info = me.first_name
                if me.username:
                    info += f" (@{me.username})"
                await client.disconnect()
                return {'name': session_name, 'info': info, 'authorized': True}
            else:
                await client.disconnect()
                return {'name': session_name, 'info': 'Not logged in', 'authorized': False}
        except Exception:
            return {'name': session_name, 'info': 'Error', 'authorized': False}