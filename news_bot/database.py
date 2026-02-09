import sqlite3
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


class NewsDatabase:
    """SQLite database to track processed news and avoid duplicates."""

    def __init__(self, db_path: str = "news_bot.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_news (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    processed_at REAL NOT NULL,
                    summary TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at
                ON processed_news(processed_at)
            """)
            conn.commit()

    @staticmethod
    def generate_id(title: str, url: str = "") -> str:
        content = f"{title}:{url}".strip().lower()
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def is_processed(self, news_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_news WHERE id = ?", (news_id,)
            )
            return cursor.fetchone() is not None

    def mark_processed(
        self, news_id: str, source: str, title: str, url: str, summary: str = ""
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR IGNORE INTO processed_news
                   (id, source, title, url, processed_at, summary)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (news_id, source, title, url, time.time(), summary),
            )
            conn.commit()

    def cleanup_old(self, max_age_days: int = 7):
        """Remove entries older than max_age_days."""
        cutoff = time.time() - (max_age_days * 86400)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM processed_news WHERE processed_at < ?", (cutoff,)
            )
            conn.commit()
            logger.info("Cleaned up old news entries (older than %d days)", max_age_days)
