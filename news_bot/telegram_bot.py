import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


class TelegramSender:
    """Sends concise news summaries to Telegram groups."""

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self._session: aiohttp.ClientSession | None = None
        self._base_url = self.API_BASE.format(token=bot_token)

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    def format_message(self, summary: str, url: str) -> str:
        """Format a news item as a concise Telegram message."""
        text = self._escape_html(summary)
        if url:
            text += f'\n<a href="{url}">Chi tiet</a>'
        return text

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters for Telegram."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    async def _api_call(self, method: str, payload: dict) -> bool:
        """Make a Telegram API call with rate limit handling."""
        try:
            session = await self._get_session()
            url = f"{self._base_url}/{method}"

            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return True
                elif resp.status == 429:
                    data = await resp.json()
                    retry_after = data.get("parameters", {}).get("retry_after", 5)
                    logger.warning("Telegram rate limit. Waiting %ds.", retry_after)
                    await asyncio.sleep(retry_after)
                    return await self._api_call(method, payload)
                else:
                    error = await resp.text()
                    logger.error("Telegram %s error %d: %s", method, resp.status, error)
                    return False

        except Exception as e:
            logger.error("Telegram %s failed: %s", method, e)
            return False

    async def send_message(self, chat_id: str, text: str) -> bool:
        """Send a text message to a specific chat."""
        if not self.is_configured or not chat_id:
            return False

        # Telegram limit: 4096 chars
        if len(text) > 4096:
            text = text[:4090] + "\n..."

        return await self._api_call("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        })

    async def send_photo(self, chat_id: str, photo_url: str, caption: str) -> bool:
        """Send a photo with caption to a specific chat."""
        if not self.is_configured or not chat_id:
            return False

        # Telegram photo caption limit: 1024 chars
        if len(caption) > 1024:
            caption = caption[:1018] + "\n..."

        return await self._api_call("sendPhoto", {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
        })

    async def send_news(
        self,
        chat_id: str,
        summary: str,
        url: str,
    ) -> bool:
        """Send a concise news summary with link."""
        message = self.format_message(summary, url)
        success = await self.send_message(chat_id, message)
        if success:
            logger.info("Sent news to %s: %s", chat_id, summary[:50])
        return success

    async def send_daily_report(self, chat_id: str, report: str) -> bool:
        """Send a daily report. Split into multiple messages if needed."""
        if not chat_id:
            return False

        # Split long reports into chunks of ~4000 chars at line boundaries
        chunks = self._split_message(report, max_len=4000)
        for chunk in chunks:
            success = await self.send_message(chat_id, chunk)
            if not success:
                return False
            await asyncio.sleep(1)
        return True

    @staticmethod
    def _split_message(text: str, max_len: int = 4000) -> list[str]:
        """Split a long message into chunks at line boundaries."""
        if len(text) <= max_len:
            return [text]

        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break

            # Find last newline before max_len
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len

            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")

        return chunks

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
