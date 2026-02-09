import asyncio
import logging
from datetime import datetime, timezone

import aiohttp

from .rss import NewsItem

logger = logging.getLogger(__name__)


class FacebookCollector:
    """Collects posts from Facebook pages via Graph API."""

    API_BASE = "https://graph.facebook.com/v19.0"

    def __init__(
        self,
        access_token: str,
        page_ids: list[str],
        poll_interval: int = 180,
    ):
        self.access_token = access_token
        self.page_ids = [p.strip() for p in page_ids if p.strip()]
        self.poll_interval = poll_interval
        self._session: aiohttp.ClientSession | None = None
        self._since_timestamps: dict[str, str] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.page_ids)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def fetch_page_posts(self, page_id: str) -> list[NewsItem]:
        """Fetch recent posts from a Facebook page."""
        items = []
        if not self.is_configured:
            return items

        try:
            session = await self._get_session()
            params = {
                "fields": "message,created_time,permalink_url,name,description",
                "limit": 10,
                "access_token": self.access_token,
            }
            if page_id in self._since_timestamps:
                params["since"] = self._since_timestamps[page_id]

            url = f"{self.API_BASE}/{page_id}/posts"
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    posts = data.get("data", [])

                    for post in posts:
                        message = post.get("message", "")
                        if not message:
                            continue

                        created_time = post.get("created_time", "")
                        permalink = post.get("permalink_url", "")
                        post_id = post.get("id", "")

                        published = None
                        if created_time:
                            try:
                                published = datetime.fromisoformat(
                                    created_time.replace("Z", "+00:00")
                                )
                            except ValueError:
                                pass

                        title = message[:120].replace("\n", " ")
                        if len(message) > 120:
                            title += "..."

                        items.append(NewsItem(
                            title=title,
                            url=permalink or f"https://facebook.com/{post_id}",
                            source=f"Facebook/{page_id}",
                            content=message,
                            published=published,
                        ))

                    # Update since timestamp
                    if posts and posts[0].get("created_time"):
                        self._since_timestamps[page_id] = posts[0]["created_time"]

                elif resp.status == 400:
                    error_data = await resp.json()
                    logger.warning(
                        "Facebook API error for page %s: %s",
                        page_id,
                        error_data.get("error", {}).get("message", "Unknown"),
                    )
                else:
                    logger.warning(
                        "Facebook API returned %d for page %s", resp.status, page_id
                    )

        except asyncio.TimeoutError:
            logger.warning("Timeout fetching Facebook page: %s", page_id)
        except Exception as e:
            logger.error("Error fetching Facebook page %s: %s", page_id, e)

        return items

    async def fetch_all(self) -> list[NewsItem]:
        """Fetch posts from all configured Facebook pages."""
        if not self.is_configured:
            logger.info("Facebook collector not configured")
            return []

        tasks = [self.fetch_page_posts(page_id) for page_id in self.page_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.error("Facebook fetch error: %s", result)

        logger.info(
            "Fetched %d posts from %d Facebook pages",
            len(all_items),
            len(self.page_ids),
        )
        return all_items

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
