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
                    summary TEXT,
                    category TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at
                ON processed_news(processed_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category
                ON processed_news(category)
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
        self,
        news_id: str,
        source: str,
        title: str,
        url: str,
        summary: str = "",
        category: str = "",
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR IGNORE INTO processed_news
                   (id, source, title, url, processed_at, summary, category)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (news_id, source, title, url, time.time(), summary, category),
            )
            conn.commit()

    def get_today_news(self, category: str = "") -> list[dict]:
        """Get all news processed today (last 24h) for a category."""
        cutoff = time.time() - 86400
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                cursor = conn.execute(
                    """SELECT source, title, url, summary, processed_at
                       FROM processed_news
                       WHERE processed_at > ? AND category = ?
                       ORDER BY processed_at DESC""",
                    (cutoff, category),
                )
            else:
                cursor = conn.execute(
                    """SELECT source, title, url, summary, category, processed_at
                       FROM processed_news
                       WHERE processed_at > ?
                       ORDER BY processed_at DESC""",
                    (cutoff,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old(self, max_age_days: int = 7):
        """Remove entries older than max_age_days."""
        cutoff = time.time() - (max_age_days * 86400)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM processed_news WHERE processed_at < ?", (cutoff,)
            )
            conn.commit()
            logger.info("Cleaned up old news entries (older than %d days)", max_age_days)
