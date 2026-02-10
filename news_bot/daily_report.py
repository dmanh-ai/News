import logging
import os
from datetime import datetime, timezone, timedelta

import aiohttp

from .config import (
    config,
    ALL_CATEGORIES,
    NEWS_CATEGORIES,
    CATEGORY_LABELS,
    CATEGORY_VN_STOCK,
    CATEGORY_WORLD_FINANCE,
    CATEGORY_CRYPTO,
    CATEGORY_GOLD,
    CATEGORY_COMMODITY,
)
from .database import NewsDatabase
from .telegram_bot import TelegramSender

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

DAILY_REPORT_PROMPT = """Ban la chuyen gia phan tich tai chinh. Viet bao cao cuoi ngay cho "{category_label}" ngay {date}.

TIN TUC HOM NAY:
{news_summaries}

{history_context}

YEU CAU:
Viet bao cao ngan gon, tap trung vao 3 phan:

1. TAC DONG TICH CUC: Nhung tin/su kien tot, co hoi, xu huong tang
2. TAC DONG TIEU CUC: Nhung rui ro, tin xau, xu huong giam
3. KHUYEN NGHI: Nen lam gi (mua/ban/giu/theo doi) voi ly do cu the

Viet bang tieng Viet, dung so lieu cu the. Format HTML cho Telegram (dung <b>, <i>).
Khong dung emoji. Moi phan chi 3-5 dong, di thang vao van de."""

COMMODITY_REPORT_PROMPT = """Ban la chuyen gia phan tich hang hoa the gioi. Ngay {date}, hay viet bang thong ke gia cac loai hang hoa chinh tren the gioi va khuyen nghi cho nha dau tu co phieu Viet Nam.

{commodity_news}

{history_context}

YEU CAU:
1. BANG GIA HANG HOA: Liet ke gia cac loai hang hoa chinh (dau tho WTI/Brent, khong khi tu nhien, than, thep, dong, nhom, cao su, gao, ca phe, duong, dau tuong, ngo, lua mi...). Neu gia hien tai, % thay doi trong ngay/tuan neu co.

2. XU HUONG: Phan tich ngan gon xu huong gia hang hoa dang tang/giam va nguyen nhan (cung cau, dia chinh tri, thoi tiet...)

3. TAC DONG DEN VIET NAM: Nhung mat hang nao anh huong truc tiep den doanh nghiep Viet Nam (thep -> HPG/HSG, dau -> GAS/PLX/BSR, cao su -> GVR/PHR, phan bon -> DPM/DCM, duong -> SBT/QNS...)

4. KHUYEN NGHI CO PHIEU VN: Cu the nen mua/ban/theo doi co phieu nao tren san Viet Nam dua tren bien dong hang hoa, voi ly do ro rang.

Viet bang tieng Viet. Format HTML cho Telegram (dung <b>, <i>).
Khong dung emoji. Di thang vao so lieu va khuyen nghi."""


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

    async def generate_commodity_report(self) -> str | None:
        """Generate daily commodity price table + VN stock recommendations."""
        # Gather commodity-related news from all categories
        all_news = self.db.get_today_news()
        commodity_kw = [
            "oil", "crude", "brent", "wti", "dau tho", "dầu thô",
            "natural gas", "khi tu nhien", "khí tự nhiên",
            "coal", "than", "steel", "thep", "thép",
            "copper", "dong", "đồng", "aluminum", "nhom", "nhôm",
            "rubber", "cao su", "rice", "gao", "gạo",
            "coffee", "ca phe", "cà phê", "sugar", "duong", "đường",
            "soybean", "dau tuong", "đậu tương", "corn", "ngo", "ngô",
            "wheat", "lua mi", "lúa mì", "palm oil", "dau co",
            "iron ore", "quang sat", "fertilizer", "phan bon", "phân bón",
            "commodity", "commodities", "hang hoa", "hàng hóa",
            "gold", "vang", "vàng", "silver", "bac", "bạc",
        ]

        commodity_items = []
        for item in all_news:
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            for kw in commodity_kw:
                if kw in text:
                    commodity_items.append(item)
                    break

        # Build summaries
        summaries = []
        for i, item in enumerate(commodity_items[:50], 1):
            summaries.append(
                f"{i}. [{item['source']}] {item['title']}\n   {item.get('summary', '')[:200]}"
            )

        news_text = "\n".join(summaries) if summaries else "Khong co tin hang hoa hom nay."
        today_str = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        history = self._load_recent_reports(CATEGORY_COMMODITY)

        prompt = COMMODITY_REPORT_PROMPT.format(
            date=today_str,
            commodity_news=news_text,
            history_context=history,
        )

        try:
            report = await self._generate_report_sonnet(prompt)
            self._save_report(CATEGORY_COMMODITY, report, today_str)
            return report
        except Exception as e:
            logger.error("Failed to generate commodity report: %s", e)
            return None

    async def run_daily_reports(self):
        """Generate and send daily reports for 4 news categories (22:00 UTC+7)."""
        logger.info("Starting daily report generation...")

        for category in NEWS_CATEGORIES:
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

    async def run_commodity_report(self):
        """Generate and send commodity price table (6:00 UTC+7)."""
        logger.info("Starting commodity report generation...")

        commodity_chat_id = config.get_chat_id(CATEGORY_COMMODITY)
        if not commodity_chat_id:
            logger.warning("No chat ID for commodity, skipping")
            return

        report = await self.generate_commodity_report()
        if report:
            header = (
                f"<b>BANG GIA HANG HOA THE GIOI</b>\n"
                f"<i>{datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M')}</i>\n\n"
            )
            await self.telegram.send_daily_report(commodity_chat_id, header + report)
            logger.info("Sent commodity report")

        logger.info("Commodity report complete.")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
