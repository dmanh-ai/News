#!/usr/bin/env python3
"""
News Summary Bot - Real-time financial news aggregator and summarizer.

Collects news from RSS feeds, X/Twitter, and Facebook,
categorizes into 4 groups (VN Stock, World Finance, Crypto, Gold),
summarizes using Haiku, sends with images to separate Telegram groups.
End-of-day analysis by Sonnet saved to daily files.

Usage:
    python -m news_bot.main                # Run continuously
    python -m news_bot.main --once         # Single collection cycle
    python -m news_bot.main --daily-report # Generate daily reports only
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta

from .collectors.rss import RSSCollector, NewsItem
from .collectors.twitter import TwitterCollector
from .collectors.facebook import FacebookCollector
from .categorizer import categorize
from .summarizer import AISummarizer
from .telegram_bot import TelegramSender
from .database import NewsDatabase
from .daily_report import DailyReporter
from .config import config, CATEGORY_LABELS

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_bot")

VN_TZ = timezone(timedelta(hours=7))


class NewsSummaryBot:
    """Main orchestrator that coordinates all components."""

    def __init__(self):
        self.db = NewsDatabase(config.db_path)

        # Collectors
        self.rss = RSSCollector(
            feeds=config.rss_feeds,
            poll_interval=config.rss_poll_interval,
        )
        self.twitter = TwitterCollector(
            bearer_token=config.twitter_bearer_token,
            accounts=config.twitter_accounts,
            poll_interval=config.twitter_poll_interval,
        )
        self.facebook = FacebookCollector(
            access_token=config.facebook_access_token,
            page_ids=config.facebook_page_ids,
            poll_interval=config.facebook_poll_interval,
        )

        # Summarizer (Haiku)
        self.summarizer = AISummarizer(
            provider=config.ai_provider,
            api_key=(
                config.anthropic_api_key
                if config.ai_provider == "anthropic"
                else config.openai_api_key
            ),
            model=config.ai_model,
        )

        # Telegram (single bot, routes to different groups)
        self.telegram = TelegramSender(bot_token=config.telegram_bot_token)

        # Daily reporter (Sonnet)
        self.reporter = DailyReporter(
            db=self.db,
            telegram=self.telegram,
            anthropic_api_key=config.anthropic_api_key,
            sonnet_model=config.sonnet_model,
            reports_dir=config.reports_dir,
        )

        self._running = False

    async def process_news_item(self, item: NewsItem) -> bool:
        """Process a single news item: dedup, categorize, summarize, send."""
        news_id = self.db.generate_id(item.title, item.url)

        if self.db.is_processed(news_id):
            return False

        # Categorize
        category = categorize(item.title, item.content, item.source)
        chat_id = config.get_chat_id(category)

        if not chat_id:
            logger.debug("No chat ID for category %s, skipping: %s", category, item.title[:50])
            return False

        # Summarize with Haiku
        summary = await self.summarizer.summarize(
            title=item.title,
            content=item.content,
            source=item.source,
        )

        # Send to the correct Telegram group (with image if available)
        success = await self.telegram.send_news(
            chat_id=chat_id,
            title=item.title,
            source=item.source,
            summary=summary,
            url=item.url,
            image_url=item.image_url,
        )

        if success:
            self.db.mark_processed(
                news_id=news_id,
                source=item.source,
                title=item.title,
                url=item.url,
                summary=summary,
                category=category,
            )

        await asyncio.sleep(1)  # Telegram rate limit
        return success

    async def collect_and_process(self, collector_name: str, items: list[NewsItem]):
        """Process a batch of news items."""
        new_count = 0
        for item in items:
            try:
                is_new = await self.process_news_item(item)
                if is_new:
                    new_count += 1
            except Exception as e:
                logger.error(
                    "Error processing item from %s: %s - %s",
                    collector_name, item.title[:50], e,
                )

        if new_count > 0:
            logger.info(
                "[%s] Processed %d new items out of %d total",
                collector_name, new_count, len(items),
            )

    # ------------------------------------------------------------------
    # ONE-SHOT MODE (GitHub Actions / cron)
    # ------------------------------------------------------------------

    async def run_once(self):
        """Run a single collection cycle and exit."""
        logger.info("=" * 60)
        logger.info("  NEWS SUMMARY BOT - Single run mode")
        logger.info("=" * 60)

        if not self.telegram.is_configured:
            logger.error("Telegram not configured!")
            return

        # Collect from all sources concurrently
        results = await asyncio.gather(
            self.rss.fetch_all(),
            self.twitter.fetch_all(),
            self.facebook.fetch_all(),
            return_exceptions=True,
        )

        for i, (name, result) in enumerate(
            zip(["RSS", "Twitter", "Facebook"], results)
        ):
            if isinstance(result, list):
                await self.collect_and_process(name, result)
            else:
                logger.error("%s fetch failed: %s", name, result)

        self.db.cleanup_old(max_age_days=7)
        await self.shutdown()
        logger.info("Single run complete.")

    # ------------------------------------------------------------------
    # DAILY REPORT MODE
    # ------------------------------------------------------------------

    async def run_daily_report(self):
        """Generate and send daily reports only."""
        logger.info("=" * 60)
        logger.info("  NEWS SUMMARY BOT - Daily report mode")
        logger.info("=" * 60)

        if not config.anthropic_api_key:
            logger.error("Anthropic API key required for daily reports (Sonnet)")
            return

        await self.reporter.run_daily_reports()
        await self.shutdown()

    # ------------------------------------------------------------------
    # CONTINUOUS MODE (VPS / Docker / local)
    # ------------------------------------------------------------------

    async def rss_loop(self):
        logger.info("Starting RSS collector (interval: %ds)", config.rss_poll_interval)
        while self._running:
            try:
                items = await self.rss.fetch_all()
                await self.collect_and_process("RSS", items)
            except Exception as e:
                logger.error("RSS loop error: %s", e)
            await asyncio.sleep(config.rss_poll_interval)

    async def twitter_loop(self):
        if not self.twitter.is_configured:
            logger.info("Twitter collector disabled (no bearer token)")
            return
        logger.info("Starting Twitter collector (interval: %ds)", config.twitter_poll_interval)
        while self._running:
            try:
                items = await self.twitter.fetch_all()
                await self.collect_and_process("Twitter", items)
            except Exception as e:
                logger.error("Twitter loop error: %s", e)
            await asyncio.sleep(config.twitter_poll_interval)

    async def facebook_loop(self):
        if not self.facebook.is_configured:
            logger.info("Facebook collector disabled")
            return
        logger.info("Starting Facebook collector (interval: %ds)", config.facebook_poll_interval)
        while self._running:
            try:
                items = await self.facebook.fetch_all()
                await self.collect_and_process("Facebook", items)
            except Exception as e:
                logger.error("Facebook loop error: %s", e)
            await asyncio.sleep(config.facebook_poll_interval)

    async def daily_report_scheduler(self):
        """Wait until daily report time, then generate reports."""
        logger.info(
            "Daily report scheduled at %02d:%02d (UTC+7)",
            config.daily_report_hour, config.daily_report_minute,
        )
        while self._running:
            now = datetime.now(VN_TZ)
            target = now.replace(
                hour=config.daily_report_hour,
                minute=config.daily_report_minute,
                second=0, microsecond=0,
            )
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            logger.info("Next daily report in %.0f minutes", wait_seconds / 60)

            await asyncio.sleep(min(wait_seconds, 3600))  # Check every hour max

            now = datetime.now(VN_TZ)
            if (now.hour == config.daily_report_hour
                    and now.minute >= config.daily_report_minute
                    and now.minute < config.daily_report_minute + 10):
                try:
                    await self.reporter.run_daily_reports()
                except Exception as e:
                    logger.error("Daily report error: %s", e)
                await asyncio.sleep(600)  # Wait 10 min to avoid re-trigger

    async def cleanup_loop(self):
        while self._running:
            await asyncio.sleep(86400)
            try:
                self.db.cleanup_old(max_age_days=7)
            except Exception as e:
                logger.error("Cleanup error: %s", e)

    async def run(self):
        """Start the bot in continuous mode."""
        self._running = True

        logger.info("=" * 60)
        logger.info("  NEWS SUMMARY BOT - Continuous mode")
        logger.info("=" * 60)
        logger.info("Telegram: %s", "OK" if self.telegram.is_configured else "NOT configured")
        logger.info("AI: %s (%s)", config.ai_provider, config.ai_model)
        logger.info("Daily report: Sonnet (%s) at %02d:%02d UTC+7",
                     config.sonnet_model, config.daily_report_hour, config.daily_report_minute)
        logger.info("RSS: %d sources", len(config.rss_feeds))
        logger.info("Twitter: %s", "OK" if self.twitter.is_configured else "disabled")
        logger.info("Facebook: %s", "OK" if self.facebook.is_configured else "disabled")
        for cat, label in CATEGORY_LABELS.items():
            chat_id = config.get_chat_id(cat)
            logger.info("  [%s] chat_id=%s", label, chat_id[:10] + "..." if chat_id else "NOT SET")
        logger.info("=" * 60)

        if not self.telegram.is_configured:
            logger.error("Telegram not configured!")
            return

        tasks = [
            asyncio.create_task(self.rss_loop()),
            asyncio.create_task(self.twitter_loop()),
            asyncio.create_task(self.facebook_loop()),
            asyncio.create_task(self.daily_report_scheduler()),
            asyncio.create_task(self.cleanup_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Bot tasks cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Shutting down...")
        self._running = False
        await self.rss.close()
        await self.twitter.close()
        await self.facebook.close()
        await self.summarizer.close()
        await self.reporter.close()
        await self.telegram.close()
        logger.info("Shutdown complete.")


def main():
    once = "--once" in sys.argv
    daily_report = "--daily-report" in sys.argv

    bot = NewsSummaryBot()

    if once:
        asyncio.run(bot.run_once())
    elif daily_report:
        asyncio.run(bot.run_daily_report())
    else:
        loop = asyncio.new_event_loop()

        def signal_handler():
            logger.info("Received shutdown signal")
            bot._running = False
            for task in asyncio.all_tasks(loop):
                task.cancel()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        try:
            loop.run_until_complete(bot.run())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()


if __name__ == "__main__":
    main()
