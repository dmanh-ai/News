import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import aiohttp
import feedparser

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    content: str
    published: datetime | None = None
    image_url: str = ""

    def __str__(self):
        return f"[{self.source}] {self.title}"


class RSSCollector:
    """Collects news from RSS feeds of major financial news sources."""

    def __init__(self, feeds: dict[str, str], poll_interval: int = 120):
        self.feeds = feeds
        self.poll_interval = poll_interval
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NewsSummaryBot/1.0)"
                },
            )
        return self._session

    @staticmethod
    def _extract_image(entry, content: str) -> str:
        """Extract image URL from RSS entry using multiple strategies."""
        # 1. media:content or media:thumbnail
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                url = media.get("url", "")
                media_type = media.get("type", "")
                if url and ("image" in media_type or media_type == ""):
                    return url

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                url = thumb.get("url", "")
                if url:
                    return url

        # 2. enclosure (common in RSS 2.0)
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                url = enc.get("href", "") or enc.get("url", "")
                enc_type = enc.get("type", "")
                if url and "image" in enc_type:
                    return url

        # 3. Extract <img src="..."> from content/description HTML
        if content:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if img_match:
                url = img_match.group(1)
                if url.startswith("http"):
                    return url

        return ""

    async def fetch_feed(self, name: str, url: str) -> list[NewsItem]:
        """Fetch and parse a single RSS feed."""
        items = []
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning("Feed %s returned status %d", name, response.status)
                    return items
                text = await response.text()

            feed = feedparser.parse(text)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title:
                    continue

                # Extract content
                content = ""
                if hasattr(entry, "summary"):
                    content = entry.summary
                elif hasattr(entry, "description"):
                    content = entry.description
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].get("value", content)

                # Extract image
                image_url = self._extract_image(entry, content)

                # Parse published date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except (TypeError, ValueError):
                        pass

                items.append(NewsItem(
                    title=title,
                    url=link,
                    source=name,
                    content=content,
                    published=published,
                    image_url=image_url,
                ))

        except asyncio.TimeoutError:
            logger.warning("Timeout fetching feed: %s", name)
        except Exception as e:
            logger.error("Error fetching feed %s: %s", name, e)

        return items

    async def fetch_all(self) -> list[NewsItem]:
        """Fetch all RSS feeds concurrently."""
        tasks = [
            self.fetch_feed(name, url) for name, url in self.feeds.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error("Feed fetch error: %s", result)

        logger.info("Fetched %d items from %d RSS feeds", len(all_items), len(self.feeds))
        return all_items

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
