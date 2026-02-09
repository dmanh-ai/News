import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # AI Summarization (supports OpenAI or Anthropic)
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")  # "openai" or "anthropic"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gpt-4o-mini")

    # X/Twitter API
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    twitter_accounts: list[str] = field(default_factory=lambda: [
        "Reuters", "Bloomberg", "CNBC", "WSJ", "FT",
        "ReutersBiz", "markets", "business",
        "cafaborsvn", "VnaborExpress",
    ])

    # Facebook
    facebook_access_token: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    facebook_page_ids: list[str] = field(default_factory=lambda: os.getenv(
        "FACEBOOK_PAGE_IDS", ""
    ).split(",") if os.getenv("FACEBOOK_PAGE_IDS") else [])

    # RSS Feeds - Major financial news sources worldwide + Vietnam
    rss_feeds: dict[str, str] = field(default_factory=lambda: {
        # === International ===
        "Reuters - Business": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "Reuters - Markets": "https://www.reutersagency.com/feed/?best-topics=markets",
        "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "CNBC - Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "CNBC - World": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "CNBC - Finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "WSJ - Markets": "https://feeds.content.wsj.com/rss/markets/main",
        "WSJ - World": "https://feeds.content.wsj.com/rss/world/main",
        "Financial Times": "https://www.ft.com/rss/home",
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "Investing.com": "https://www.investing.com/rss/news.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "The Economist": "https://www.economist.com/finance-and-economics/rss.xml",
        "Forbes": "https://www.forbes.com/money/feed/",
        "Business Insider": "https://markets.businessinsider.com/rss/news",
        "FX Street": "https://www.fxstreet.com/rss/news",
        "Forex Factory": "https://www.forexfactory.com/rss",
        "Zero Hedge": "https://feeds.feedburner.com/zerohedge/feed",
        "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
        # === Asia ===
        "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",
        "South China Morning Post": "https://www.scmp.com/rss/91/feed",
        # === Vietnam ===
        "VnExpress - Kinh Doanh": "https://vnexpress.net/rss/kinh-doanh.rss",
        "VnExpress - The Gioi": "https://vnexpress.net/rss/the-gioi.rss",
        "CafeF": "https://cafef.vn/rss/trang-chu.rss",
        "CafeF - Chung Khoan": "https://cafef.vn/rss/chung-khoan.rss",
        "CafeF - Vi Mo": "https://cafef.vn/rss/vi-mo-dau-tu.rss",
        "CafeF - Tai Chinh QT": "https://cafef.vn/rss/tai-chinh-quoc-te.rss",
        "VietStock": "https://vietstock.vn/rss/tai-chinh.rss",
        "VietStock - TTCK": "https://vietstock.vn/rss/chung-khoan.rss",
        "Thanh Nien - Kinh Te": "https://thanhnien.vn/rss/kinh-te.rss",
        "Tuoi Tre - Kinh Doanh": "https://tuoitre.vn/rss/kinh-doanh.rss",
        "Nguoi Lao Dong - Kinh Te": "https://nld.com.vn/rss/kinh-te.rss",
        "Dan Tri - Kinh Doanh": "https://dantri.com.vn/rss/kinh-doanh.rss",
        "VTV - Kinh Te": "https://vtv.vn/kinh-te.rss",
        "TBKTSG": "https://thesaigontimes.vn/feed/",
    })

    # Polling intervals (seconds)
    rss_poll_interval: int = int(os.getenv("RSS_POLL_INTERVAL", "120"))  # 2 minutes
    twitter_poll_interval: int = int(os.getenv("TWITTER_POLL_INTERVAL", "60"))
    facebook_poll_interval: int = int(os.getenv("FACEBOOK_POLL_INTERVAL", "180"))

    # Database
    db_path: str = os.getenv("DB_PATH", "news_bot.db")

    # Summarization language
    summary_language: str = os.getenv("SUMMARY_LANGUAGE", "vi")  # Vietnamese by default


config = Config()
