import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)


class TelegramSender:
    """Sends formatted news summaries to Telegram."""

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._session: aiohttp.ClientSession | None = None
        self._base_url = self.API_BASE.format(token=bot_token)

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    def format_message(
        self, title: str, source: str, summary: str, url: str
    ) -> str:
        """Format a news item as a Telegram message with HTML."""
        parts = [
            f"<b>📌 {self._escape_html(title)}</b>",
            "",
            f"🔗 <i>Nguồn: {self._escape_html(source)}</i>",
            "",
            self._escape_html(summary),
        ]

        if url:
            parts.append("")
            parts.append(f'👉 <a href="{url}">Đọc thêm</a>')

        return "\n".join(parts)

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters for Telegram."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    async def send_message(self, text: str) -> bool:
        """Send a message to the configured Telegram chat."""
        if not self.is_configured:
            logger.warning("Telegram not configured. Message not sent.")
            return False

        try:
            session = await self._get_session()
            url = f"{self._base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }

            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    return True
                elif resp.status == 429:
                    # Rate limited - wait and retry
                    data = await resp.json()
                    retry_after = data.get("parameters", {}).get("retry_after", 5)
                    logger.warning(
                        "Telegram rate limit. Waiting %d seconds.", retry_after
                    )
                    await asyncio.sleep(retry_after)
                    return await self.send_message(text)
                else:
                    error = await resp.text()
                    logger.error("Telegram API error %d: %s", resp.status, error)
                    return False

        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            return False

    async def send_news(
        self, title: str, source: str, summary: str, url: str
    ) -> bool:
        """Format and send a news item."""
        message = self.format_message(title, source, summary, url)

        # Telegram message limit is 4096 chars
        if len(message) > 4096:
            message = message[:4090] + "\n..."

        success = await self.send_message(message)
        if success:
            logger.info("Sent news to Telegram: %s", title[:60])
        return success

    async def send_startup_message(self):
        """Send a startup notification."""
        message = (
            "🤖 <b>News Summary Bot đã khởi động!</b>\n\n"
            "Bot sẽ tự động thu thập và tóm tắt tin tức tài chính từ:\n"
            "• 📰 RSS Feeds (Reuters, Bloomberg, CNBC, CafeF, VnExpress...)\n"
            "• 🐦 X/Twitter\n"
            "• 📘 Facebook\n\n"
            "Tin tức sẽ được gửi ngay khi phát hiện."
        )
        await self.send_message(message)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
