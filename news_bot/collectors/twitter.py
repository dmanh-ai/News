import asyncio
import logging
from datetime import datetime, timezone

import aiohttp

from .rss import NewsItem

logger = logging.getLogger(__name__)


class TwitterCollector:
    """Collects financial news tweets from X/Twitter API v2."""

    API_BASE = "https://api.twitter.com/2"

    def __init__(
        self,
        bearer_token: str,
        accounts: list[str],
        poll_interval: int = 60,
    ):
        self.bearer_token = bearer_token
        self.accounts = accounts
        self.poll_interval = poll_interval
        self._session: aiohttp.ClientSession | None = None
        self._user_ids: dict[str, str] = {}
        self._since_ids: dict[str, str] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.bearer_token)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Authorization": f"Bearer {self.bearer_token}"},
            )
        return self._session

    async def _resolve_user_id(self, username: str) -> str | None:
        """Resolve a Twitter username to user ID."""
        if username in self._user_ids:
            return self._user_ids[username]

        try:
            session = await self._get_session()
            url = f"{self.API_BASE}/users/by/username/{username}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    user_id = data.get("data", {}).get("id")
                    if user_id:
                        self._user_ids[username] = user_id
                        return user_id
                elif resp.status == 429:
                    logger.warning("Twitter rate limit hit for user lookup: %s", username)
                else:
                    logger.warning("Failed to resolve Twitter user %s: %d", username, resp.status)
        except Exception as e:
            logger.error("Error resolving Twitter user %s: %s", username, e)

        return None

    async def fetch_user_tweets(self, username: str) -> list[NewsItem]:
        """Fetch recent tweets from a specific user."""
        items = []
        if not self.is_configured:
            return items

        user_id = await self._resolve_user_id(username)
        if not user_id:
            return items

        try:
            session = await self._get_session()
            params = {
                "max_results": 10,
                "tweet.fields": "created_at,text,entities",
                "exclude": "retweets",
            }
            if username in self._since_ids:
                params["since_id"] = self._since_ids[username]

            url = f"{self.API_BASE}/users/{user_id}/tweets"
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tweets = data.get("data", [])
                    meta = data.get("meta", {})

                    if meta.get("newest_id"):
                        self._since_ids[username] = meta["newest_id"]

                    for tweet in tweets:
                        text = tweet.get("text", "")
                        tweet_id = tweet.get("id", "")
                        created_at = tweet.get("created_at")

                        published = None
                        if created_at:
                            try:
                                published = datetime.fromisoformat(
                                    created_at.replace("Z", "+00:00")
                                )
                            except ValueError:
                                pass

                        # Extract URLs from tweet
                        tweet_url = f"https://x.com/{username}/status/{tweet_id}"

                        items.append(NewsItem(
                            title=f"@{username}: {text[:100]}...",
                            url=tweet_url,
                            source=f"X/@{username}",
                            content=text,
                            published=published,
                        ))

                elif resp.status == 429:
                    retry_after = resp.headers.get("x-rate-limit-reset")
                    logger.warning(
                        "Twitter rate limit for %s. Reset: %s", username, retry_after
                    )
                else:
                    logger.warning(
                        "Twitter API error for %s: %d", username, resp.status
                    )

        except asyncio.TimeoutError:
            logger.warning("Timeout fetching tweets for %s", username)
        except Exception as e:
            logger.error("Error fetching tweets for %s: %s", username, e)

        return items

    async def fetch_all(self) -> list[NewsItem]:
        """Fetch tweets from all configured accounts."""
        if not self.is_configured:
            logger.info("Twitter collector not configured (no bearer token)")
            return []

        all_items = []
        # Process sequentially to avoid rate limits
        for username in self.accounts:
            items = await self.fetch_user_tweets(username)
            all_items.extend(items)
            await asyncio.sleep(1)  # Rate limit courtesy delay

        logger.info("Fetched %d tweets from %d accounts", len(all_items), len(self.accounts))
        return all_items

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
