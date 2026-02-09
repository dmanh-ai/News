import logging
import re

import aiohttp

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tài chính. Nhiệm vụ của bạn là tóm tắt tin tức tài chính một cách ngắn gọn, chính xác.

Quy tắc:
1. Tóm tắt trong 2-4 câu bằng tiếng Việt
2. Nêu rõ thông tin quan trọng nhất: số liệu, tỷ lệ, xu hướng
3. Phân loại tin: 🏦 Vĩ mô | 📊 Chứng khoán | 💰 Tiền tệ | 🛢️ Hàng hóa | 🏢 Doanh nghiệp | 🌍 Quốc tế | 🇻🇳 Việt Nam
4. Đánh giá tác động: 🔴 Tiêu cực | 🟢 Tích cực | 🟡 Trung tính
5. Nếu tin bằng tiếng Anh, dịch và tóm tắt sang tiếng Việt"""


class AISummarizer:
    """Summarizes news articles using OpenAI or Anthropic APIs."""

    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        model: str = "gpt-4o-mini",
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._session: aiohttp.ClientSession | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
            )
        return self._session

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:3000]  # Limit content length

    async def summarize(self, title: str, content: str, source: str) -> str:
        """Summarize a news article."""
        if not self.is_configured:
            return self._fallback_summary(title, content, source)

        clean_content = self._clean_html(content)
        user_message = (
            f"Nguồn: {source}\n"
            f"Tiêu đề: {title}\n"
            f"Nội dung: {clean_content}"
        )

        try:
            if self.provider == "anthropic":
                return await self._summarize_anthropic(user_message)
            else:
                return await self._summarize_openai(user_message)
        except Exception as e:
            logger.error("AI summarization failed: %s", e)
            return self._fallback_summary(title, content, source)

    async def _summarize_openai(self, user_message: str) -> str:
        session = await self._get_session()
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 500,
                "temperature": 0.3,
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                error = await resp.text()
                logger.error("OpenAI API error %d: %s", resp.status, error)
                raise RuntimeError(f"OpenAI API error: {resp.status}")

    async def _summarize_anthropic(self, user_message: str) -> str:
        session = await self._get_session()
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": user_message},
                ],
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["content"][0]["text"].strip()
            else:
                error = await resp.text()
                logger.error("Anthropic API error %d: %s", resp.status, error)
                raise RuntimeError(f"Anthropic API error: {resp.status}")

    def _fallback_summary(self, title: str, content: str, source: str) -> str:
        """Simple fallback when AI is not available."""
        clean = self._clean_html(content)
        if len(clean) > 200:
            clean = clean[:200] + "..."
        return f"📰 {title}\n\n{clean}"

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
