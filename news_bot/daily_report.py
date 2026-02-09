import logging
import os
from datetime import datetime, timezone, timedelta

import aiohttp

from .config import (
    config,
    ALL_CATEGORIES,
    CATEGORY_LABELS,
    CATEGORY_VN_STOCK,
    CATEGORY_WORLD_FINANCE,
    CATEGORY_CRYPTO,
    CATEGORY_GOLD,
)
from .database import NewsDatabase
from .telegram_bot import TelegramSender

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

DAILY_REPORT_PROMPT = """Ban la chuyen gia phan tich tai chinh cap cao. Hay viet bao cao tong hop cuoi ngay cho danh muc "{category_label}".

DU LIEU HOM NAY ({date}):
{news_summaries}

{history_context}

YEU CAU BAO CAO:
1. TONG QUAN: Tom tat xu huong chinh trong ngay (3-5 cau)
2. TIN NONG: 3-5 tin quan trong nhat va tac dong
3. PHAN TICH: Xau chuoi cac su kien, nhan dinh nguyen nhan va he qua
4. NHAN DINH: Dua ra du bao ngan han (1-3 ngay toi) dua tren xu huong
5. KHUYEN NGHI: Hanh dong nen lam (mua/ban/giu/theo doi gi)

Viet bang tieng Viet, su dung so lieu cu the. Format HTML cho Telegram (dung <b>, <i>, <code>).
Bat dau bang emoji phu hop cho tung muc."""


class DailyReporter:
    """Generates end-of-day analysis reports using Claude Sonnet."""

    def __init__(
        self,
        db: NewsDatabase,
        telegram: TelegramSender,
        anthropic_api_key: str,
        sonnet_model: str,
        reports_dir: str,
    ):
        self.db = db
        self.telegram = telegram
        self.anthropic_api_key = anthropic_api_key
        self.sonnet_model = sonnet_model
        self.reports_dir = reports_dir
        self._session: aiohttp.ClientSession | None = None

        # Ensure reports directory exists
        os.makedirs(reports_dir, exist_ok=True)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120),
            )
        return self._session

    def _load_recent_reports(self, category: str, days: int = 3) -> str:
        """Load recent daily reports for context."""
        reports = []
        today = datetime.now(VN_TZ).date()
        for i in range(1, days + 1):
            date = today - timedelta(days=i)
            filename = f"{category}_{date.isoformat()}.txt"
            filepath = os.path.join(self.reports_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                reports.append(f"--- Bao cao ngay {date.isoformat()} ---\n{content[:2000]}")

        if reports:
            return "LICH SU BAO CAO GAN DAY:\n" + "\n\n".join(reports)
        return "Chua co bao cao truoc do."

    def _save_report(self, category: str, report: str, date: str):
        """Save daily report to file."""
        filename = f"{category}_{date}.txt"
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Saved daily report: %s", filepath)

    async def _generate_report_sonnet(self, prompt: str) -> str:
        """Call Claude Sonnet for analysis."""
        session = await self._get_session()
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.sonnet_model,
                "max_tokens": 4000,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["content"][0]["text"].strip()
            else:
                error = await resp.text()
                logger.error("Sonnet API error %d: %s", resp.status, error)
                raise RuntimeError(f"Sonnet API error: {resp.status}")

    async def generate_category_report(self, category: str) -> str | None:
        """Generate a daily report for one category."""
        news_items = self.db.get_today_news(category)

        if not news_items:
            logger.info("No news today for category: %s", category)
            return None

        # Build news summaries text
        summaries = []
        for i, item in enumerate(news_items[:50], 1):  # Max 50 items
            summaries.append(
                f"{i}. [{item['source']}] {item['title']}\n   {item.get('summary', '')[:200]}"
            )

        news_text = "\n".join(summaries)
        today_str = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        history = self._load_recent_reports(category)
        category_label = CATEGORY_LABELS.get(category, category)

        prompt = DAILY_REPORT_PROMPT.format(
            category_label=category_label,
            date=today_str,
            news_summaries=news_text,
            history_context=history,
        )

        try:
            report = await self._generate_report_sonnet(prompt)
            self._save_report(category, report, today_str)
            return report
        except Exception as e:
            logger.error("Failed to generate report for %s: %s", category, e)
            return None

    async def run_daily_reports(self):
        """Generate and send daily reports for all categories."""
        logger.info("Starting daily report generation...")

        for category in ALL_CATEGORIES:
            chat_id = config.get_chat_id(category)
            if not chat_id:
                logger.warning("No chat ID for category %s, skipping report", category)
                continue

            report = await self.generate_category_report(category)
            if report:
                header = (
                    f"<b>BAO CAO CUOI NGAY - "
                    f"{CATEGORY_LABELS.get(category, category).upper()}</b>\n"
                    f"<i>{datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M')}</i>\n\n"
                )
                await self.telegram.send_daily_report(chat_id, header + report)
                logger.info("Sent daily report for %s", category)

        logger.info("Daily reports complete.")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
