#!/usr/bin/env python3
"""
News Summary Bot - Real-time financial news aggregator and summarizer.

Collects news from RSS feeds, X/Twitter, and Facebook,
summarizes them using AI, and sends to Telegram.
"""

import asyncio
import logging
import signal
import sys

from .collectors.rss import RSSCollector, NewsItem
from .collectors.twitter import TwitterCollector
from .collectors.facebook import FacebookCollector
from .summarizer import AISummarizer
from .telegram_bot import TelegramSender
from .database import NewsDatabase
from .config import config

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_bot")


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

        # Summarizer
        self.summarizer = AISummarizer(
            provider=config.ai_provider,
            api_key=(
                config.anthropic_api_key
                if config.ai_provider == "anthropic"
                else config.openai_api_key
            ),
            model=config.ai_model,
        )

        # Telegram
        self.telegram = TelegramSender(
            bot_token=config.telegram_bot_token,
            chat_id=config.telegram_chat_id,
        )

        self._running = False

    async def process_news_item(self, item: NewsItem) -> bool:
        """Process a single news item: check duplicate, summarize, send."""
        news_id = self.db.generate_id(item.title, item.url)

        if self.db.is_processed(news_id):
            return False

        # Summarize
        summary = await self.summarizer.summarize(
            title=item.title,
            content=item.content,
            source=item.source,
        )

        # Send to Telegram
        success = await self.telegram.send_news(
            title=item.title,
            source=item.source,
            summary=summary,
            url=item.url,
        )

        if success:
            self.db.mark_processed(
                news_id=news_id,
                source=item.source,
                title=item.title,
                url=item.url,
                summary=summary,
            )

        # Small delay to avoid Telegram rate limits
        await asyncio.sleep(1)
        return success

    async def collect_and_process(
        self, collector_name: str, items: list[NewsItem]
    ):
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

    async def rss_loop(self):
        """Continuously poll RSS feeds."""
        logger.info("Starting RSS collector (interval: %ds)", config.rss_poll_interval)
        while self._running:
            try:
                items = await self.rss.fetch_all()
                await self.collect_and_process("RSS", items)
            except Exception as e:
                logger.error("RSS loop error: %s", e)

            await asyncio.sleep(config.rss_poll_interval)

    async def twitter_loop(self):
        """Continuously poll Twitter."""
        if not self.twitter.is_configured:
            logger.info("Twitter collector disabled (no bearer token)")
            return

        logger.info(
            "Starting Twitter collector (interval: %ds)", config.twitter_poll_interval
        )
        while self._running:
            try:
                items = await self.twitter.fetch_all()
                await self.collect_and_process("Twitter", items)
            except Exception as e:
                logger.error("Twitter loop error: %s", e)

            await asyncio.sleep(config.twitter_poll_interval)

    async def facebook_loop(self):
        """Continuously poll Facebook."""
        if not self.facebook.is_configured:
            logger.info("Facebook collector disabled (not configured)")
            return

        logger.info(
            "Starting Facebook collector (interval: %ds)", config.facebook_poll_interval
        )
        while self._running:
            try:
                items = await self.facebook.fetch_all()
                await self.collect_and_process("Facebook", items)
            except Exception as e:
                logger.error("Facebook loop error: %s", e)

            await asyncio.sleep(config.facebook_poll_interval)

    async def cleanup_loop(self):
        """Periodically clean up old database entries."""
        while self._running:
            await asyncio.sleep(86400)  # Daily
            try:
                self.db.cleanup_old(max_age_days=7)
            except Exception as e:
                logger.error("Cleanup error: %s", e)

    async def run(self):
        """Start the bot."""
        self._running = True

        logger.info("=" * 60)
        logger.info("  NEWS SUMMARY BOT - Starting up")
        logger.info("=" * 60)
        logger.info("Telegram: %s", "configured" if self.telegram.is_configured else "NOT configured")
        logger.info("AI Summarizer: %s (%s)", config.ai_provider, config.ai_model)
        logger.info("RSS feeds: %d sources", len(config.rss_feeds))
        logger.info("Twitter: %s", "configured" if self.twitter.is_configured else "NOT configured")
        logger.info("Facebook: %s", "configured" if self.facebook.is_configured else "NOT configured")
        logger.info("=" * 60)

        if not self.telegram.is_configured:
            logger.error(
                "Telegram is not configured! Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )
            return

        # Send startup message
        await self.telegram.send_startup_message()

        # Run all loops concurrently
        tasks = [
            asyncio.create_task(self.rss_loop()),
            asyncio.create_task(self.twitter_loop()),
            asyncio.create_task(self.facebook_loop()),
            asyncio.create_task(self.cleanup_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Bot tasks cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self._running = False
        await self.rss.close()
        await self.twitter.close()
        await self.facebook.close()
        await self.summarizer.close()
        await self.telegram.close()
        logger.info("Shutdown complete.")


def main():
    bot = NewsSummaryBot()

    # Handle signals for graceful shutdown
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
