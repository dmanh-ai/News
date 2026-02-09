import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


# News categories
CATEGORY_VN_STOCK = "vn_stock"
CATEGORY_WORLD_FINANCE = "world_finance"
CATEGORY_CRYPTO = "crypto"
CATEGORY_GOLD = "gold"
CATEGORY_COMMODITY = "commodity"

# Categories that receive real-time news (limited to DAILY_NEWS_LIMIT per day)
NEWS_CATEGORIES = [CATEGORY_VN_STOCK, CATEGORY_WORLD_FINANCE, CATEGORY_CRYPTO, CATEGORY_GOLD]

# All categories including commodity (commodity only gets daily report, no real-time news)
ALL_CATEGORIES = [CATEGORY_VN_STOCK, CATEGORY_WORLD_FINANCE, CATEGORY_CRYPTO, CATEGORY_GOLD, CATEGORY_COMMODITY]

CATEGORY_LABELS = {
    CATEGORY_VN_STOCK: "Chung Khoan Viet Nam",
    CATEGORY_WORLD_FINANCE: "Tai Chinh The Gioi",
    CATEGORY_CRYPTO: "Crypto",
    CATEGORY_GOLD: "Vang",
    CATEGORY_COMMODITY: "Hang Hoa The Gioi",
}

# Max news per category per day
DAILY_NEWS_LIMIT = int(os.getenv("DAILY_NEWS_LIMIT", "20"))


@dataclass
class Config:
    # Telegram - one bot, 5 separate group chat IDs
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_vn_stock: str = os.getenv("TELEGRAM_CHAT_VN_STOCK", "")
    telegram_chat_world_finance: str = os.getenv("TELEGRAM_CHAT_WORLD_FINANCE", "")
    telegram_chat_crypto: str = os.getenv("TELEGRAM_CHAT_CRYPTO", "")
    telegram_chat_gold: str = os.getenv("TELEGRAM_CHAT_GOLD", "")
    telegram_chat_commodity: str = os.getenv("TELEGRAM_CHAT_COMMODITY", "")

    # AI Summarization - Haiku for news summaries
    ai_provider: str = os.getenv("AI_PROVIDER", "anthropic")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "claude-haiku-4-5-20251001")

    # Daily report - Sonnet for end-of-day analysis
    sonnet_model: str = os.getenv("SONNET_MODEL", "claude-sonnet-4-5-20250929")

    # Daily report time (HH:MM in UTC+7)
    daily_report_hour: int = int(os.getenv("DAILY_REPORT_HOUR", "22"))
    daily_report_minute: int = int(os.getenv("DAILY_REPORT_MINUTE", "0"))

    # Daily reports storage directory
    reports_dir: str = os.getenv("REPORTS_DIR", "daily_reports")

    # X/Twitter API
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    twitter_accounts: list[str] = field(default_factory=lambda: [
        # === Major Wire Services ===
        "Reuters", "ReutersBiz", "ReutersGMF",
        "AP", "AFP",
        # === US Business & Markets ===
        "Bloomberg", "BloombergTV", "BBGMarkets",
        "CNBC", "CNBCnow", "SquawkCNBC",
        "WSJ", "WSJmarkets", "WSJDealJournal",
        "FT", "FTMarkets", "ftfinancenews",
        "MarketWatch", "YahooFinance",
        "business", "ForbesBusiness",
        "TheEconomist",
        # === Markets & Trading ===
        "markets", "Investingcom", "SeekingAlpha",
        "RealVisionTV",
        "unusual_whales", "DeItaone",
        "Schuldensuehner", "NorthmanTrader",
        # === Central Banks & Policy ===
        "federalreserve", "BankofEngland",
        # === Macro & Economics ===
        "MacroAlf", "LynAldenContact", "EPBResearch",
        # === Crypto & Fintech ===
        "CoinDesk", "Cointelegraph", "WuBlockchain",
        # === Asia ===
        "NikkeiAsia", "SCMPNews",
        "GlobalTimes_News",
        # === Vietnam ===
        "VnExpress_en", "VietnamNewss",
        # === Commodities & Energy ===
        "JavierBlas", "Ed_Crooks",
        # === Gold ===
        "GoldTelegraph_", "KitcoNewsNOW",
    ])

    # Facebook
    facebook_access_token: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    facebook_page_ids: list[str] = field(default_factory=lambda: os.getenv(
        "FACEBOOK_PAGE_IDS", ""
    ).split(",") if os.getenv("FACEBOOK_PAGE_IDS") else [])

    # RSS Feeds - 120+ financial news sources worldwide + Vietnam
    rss_feeds: dict[str, str] = field(default_factory=lambda: {

        # =============================================
        # WIRE SERVICES & MAJOR NEWS AGENCIES
        # =============================================
        "Reuters - Business": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "Reuters - Markets": "https://www.reutersagency.com/feed/?best-topics=markets",
        "Reuters - World": "https://www.reutersagency.com/feed/?best-topics=world",
        "AP - Business": "https://rsshub.app/apnews/topics/business",

        # =============================================
        # US FINANCIAL NEWS
        # =============================================
        "Bloomberg - Markets": "https://feeds.bloomberg.com/markets/news.rss",
        "Bloomberg - Politics": "https://feeds.bloomberg.com/politics/news.rss",
        "Bloomberg - Technology": "https://feeds.bloomberg.com/technology/news.rss",
        "Bloomberg - Wealth": "https://feeds.bloomberg.com/wealth/news.rss",
        "CNBC - Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "CNBC - World": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "CNBC - Finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "CNBC - Economy": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
        "CNBC - Earnings": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839135",
        "CNBC - Commodities": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=18266436",
        "CNBC - Bonds": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=21014093",
        "WSJ - Markets": "https://feeds.content.wsj.com/rss/markets/main",
        "WSJ - World": "https://feeds.content.wsj.com/rss/world/main",
        "WSJ - Business": "https://feeds.content.wsj.com/rss/RSSWorldnews.xml",
        "WSJ - Opinion": "https://feeds.content.wsj.com/rss/RSSOpinion.xml",
        "FT - Home": "https://www.ft.com/rss/home",
        "FT - World": "https://www.ft.com/world?format=rss",
        "FT - Markets": "https://www.ft.com/markets?format=rss",
        "FT - Companies": "https://www.ft.com/companies?format=rss",
        "MarketWatch - Top": "https://www.marketwatch.com/rss/topstories",
        "MarketWatch - Markets": "https://www.marketwatch.com/rss/marketpulse",
        "MarketWatch - Bulletins": "https://www.marketwatch.com/rss/realtimeheadlines",
        "Investing.com": "https://www.investing.com/rss/news.rss",
        "Investing.com - Forex": "https://www.investing.com/rss/forex.rss",
        "Investing.com - Commodities": "https://www.investing.com/rss/commodities.rss",
        "Investing.com - Stock Market": "https://www.investing.com/rss/stock_market.rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "The Economist": "https://www.economist.com/finance-and-economics/rss.xml",
        "The Economist - Business": "https://www.economist.com/business/rss.xml",
        "Forbes - Money": "https://www.forbes.com/money/feed/",
        "Forbes - Markets": "https://www.forbes.com/investing/feed/",
        "Forbes - Business": "https://www.forbes.com/business/feed/",
        "Business Insider - Markets": "https://markets.businessinsider.com/rss/news",
        "Barrons": "https://www.barrons.com/feed",

        # =============================================
        # FOREX & TRADING
        # =============================================
        "FX Street - News": "https://www.fxstreet.com/rss/news",
        "FX Street - Analysis": "https://www.fxstreet.com/rss/analysis",
        "FX Street - Central Banks": "https://www.fxstreet.com/rss/central-banks",
        "Forex Factory": "https://www.forexfactory.com/rss",
        "DailyFX": "https://www.dailyfx.com/feeds/market-news",
        "Forex Live": "https://www.forexlive.com/feed",
        "Trading Economics": "https://tradingeconomics.com/rss/news.aspx",

        # =============================================
        # COMMODITIES & ENERGY & GOLD
        # =============================================
        "OilPrice.com": "https://oilprice.com/rss/main",
        "Mining.com": "https://www.mining.com/feed/",
        "Rigzone": "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
        "Hellenic Shipping News": "https://www.hellenicshippingnews.com/feed/",
        "Platts": "https://www.spglobal.com/commodityinsights/en/rss-feed/market-insights",
        "Kitco - Gold": "https://www.kitco.com/rss/gold.rss",

        # =============================================
        # ALTERNATIVE & ANALYSIS
        # =============================================
        "Zero Hedge": "https://feeds.feedburner.com/zerohedge/feed",
        "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
        "Seeking Alpha - Top": "https://seekingalpha.com/feed.xml",
        "Wolf Street": "https://wolfstreet.com/feed/",
        "Mish Talk": "https://mishtalk.com/feed",
        "Calculated Risk": "https://www.calculatedriskblog.com/feeds/posts/default?alt=rss",

        # =============================================
        # CRYPTO & DIGITAL ASSETS
        # =============================================
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "CoinTelegraph": "https://cointelegraph.com/rss",
        "The Block": "https://www.theblock.co/rss.xml",
        "Decrypt": "https://decrypt.co/feed",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",

        # =============================================
        # CENTRAL BANKS & POLICY
        # =============================================
        "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
        "ECB": "https://www.ecb.europa.eu/rss/press.html",
        "IMF Blog": "https://www.imf.org/en/Blogs/rss",
        "World Bank": "https://blogs.worldbank.org/feed",
        "BIS": "https://www.bis.org/doclist/bis_fsi_publs.rss",

        # =============================================
        # EUROPE
        # =============================================
        "Reuters UK": "https://feeds.reuters.com/reuters/UKBankingFinancial",
        "City AM": "https://www.cityam.com/feed/",
        "Les Echos": "https://www.lesechos.fr/rss/rss_une.xml",
        "Handelsblatt": "https://www.handelsblatt.com/contentexport/feed/top",
        "Euronews Business": "https://www.euronews.com/rss?level=vertical&name=business",

        # =============================================
        # ASIA PACIFIC
        # =============================================
        "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",
        "SCMP - Business": "https://www.scmp.com/rss/91/feed",
        "SCMP - Economy": "https://www.scmp.com/rss/5/feed",
        "Channel News Asia - Business": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
        "Straits Times - Business": "https://www.straitstimes.com/news/business/rss.xml",
        "Bangkok Post - Business": "https://www.bangkokpost.com/rss/data/business.xml",
        "Jakarta Post - Business": "https://www.thejakartapost.com/bisnistech/feed",
        "Korea Herald - Business": "https://www.koreaherald.com/common/rss_xml.php?ct=102",
        "Taipei Times - Business": "https://www.taipeitimes.com/xml/business.rss",
        "Livemint India": "https://www.livemint.com/rss/markets",
        "Economic Times India": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "Business Standard India": "https://www.business-standard.com/rss/markets-106.rss",
        "China Daily - Business": "https://www.chinadaily.com.cn/rss/business_rss.xml",
        "Global Times - Business": "https://www.globaltimes.cn/rss/outbrain.xml",
        "Asia Times": "https://asiatimes.com/feed/",
        "The Diplomat": "https://thediplomat.com/feed/",

        # =============================================
        # MIDDLE EAST & AFRICA
        # =============================================
        "Al Jazeera - Economy": "https://www.aljazeera.com/xml/rss/all.xml",
        "Gulf News - Business": "https://gulfnews.com/business/rss",
        "Arab News - Economy": "https://www.arabnews.com/cat/3/rss.xml",

        # =============================================
        # LATIN AMERICA
        # =============================================
        "Reuters - LATAM": "https://www.reutersagency.com/feed/?best-regions=latin-america",
        "BNAmericas": "https://www.bnamericas.com/en/rss",

        # =============================================
        # VIETNAM - Comprehensive
        # =============================================
        "VnExpress - Kinh Doanh": "https://vnexpress.net/rss/kinh-doanh.rss",
        "VnExpress - The Gioi": "https://vnexpress.net/rss/the-gioi.rss",
        "VnExpress - Chung Khoan": "https://vnexpress.net/rss/kinh-doanh/chung-khoan.rss",
        "VnExpress - Bat Dong San": "https://vnexpress.net/rss/kinh-doanh/bat-dong-san.rss",
        "VnExpress - Vi Mo": "https://vnexpress.net/rss/kinh-doanh/vi-mo.rss",
        "VnExpress - Tai Chinh": "https://vnexpress.net/rss/kinh-doanh/tai-chinh.rss",
        "CafeF - Trang Chu": "https://cafef.vn/rss/trang-chu.rss",
        "CafeF - Chung Khoan": "https://cafef.vn/rss/chung-khoan.rss",
        "CafeF - Vi Mo": "https://cafef.vn/rss/vi-mo-dau-tu.rss",
        "CafeF - Tai Chinh QT": "https://cafef.vn/rss/tai-chinh-quoc-te.rss",
        "CafeF - Doanh Nghiep": "https://cafef.vn/rss/doanh-nghiep.rss",
        "CafeF - Bat Dong San": "https://cafef.vn/rss/bat-dong-san.rss",
        "CafeF - Ngan Hang": "https://cafef.vn/rss/ngan-hang.rss",
        "CafeF - Hang Hoa": "https://cafef.vn/rss/hang-hoa-nguyen-lieu.rss",
        "CafeF - Vang": "https://cafef.vn/rss/vang.rss",
        "CafeF - Tien Te": "https://cafef.vn/rss/tien-te.rss",
        "VietStock - Tai Chinh": "https://vietstock.vn/rss/tai-chinh.rss",
        "VietStock - TTCK": "https://vietstock.vn/rss/chung-khoan.rss",
        "VietStock - Doanh Nghiep": "https://vietstock.vn/rss/doanh-nghiep.rss",
        "Thanh Nien - Kinh Te": "https://thanhnien.vn/rss/kinh-te.rss",
        "Thanh Nien - Tai Chinh": "https://thanhnien.vn/rss/tai-chinh-kinh-doanh.rss",
        "Tuoi Tre - Kinh Doanh": "https://tuoitre.vn/rss/kinh-doanh.rss",
        "Tuoi Tre - Tai Chinh": "https://tuoitre.vn/rss/tai-chinh.rss",
        "Nguoi Lao Dong - Kinh Te": "https://nld.com.vn/rss/kinh-te.rss",
        "Dan Tri - Kinh Doanh": "https://dantri.com.vn/rss/kinh-doanh.rss",
        "Dan Tri - BDS": "https://dantri.com.vn/rss/bat-dong-san.rss",
        "VTV - Kinh Te": "https://vtv.vn/kinh-te.rss",
        "VTV - The Gioi": "https://vtv.vn/the-gioi.rss",
        "TBKTSG": "https://thesaigontimes.vn/feed/",
        "BizLive": "https://bizlive.vn/rss/home.rss",
        "Bao Dau Tu": "https://baodautu.vn/rss/home.rss",
        "Bao Dau Tu - TTCK": "https://baodautu.vn/rss/chung-khoan-d4.rss",
        "Bao Dau Tu - Ngan Hang": "https://baodautu.vn/rss/ngan-hang-d7.rss",
        "NDH": "https://ndh.vn/rss/home.rss",
        "TCTC Online": "https://thoibaotaichinhvietnam.vn/rss/home.rss",
        "Tin Nhanh CK": "https://tinnhanhchungkhoan.vn/rss/home.rss",
        "SBV (Ngan Hang NN)": "https://www.sbv.gov.vn/webcenter/portal/vi/menu/trangchu/ttsk/rss",
        "VnEconomy": "https://vneconomy.vn/tai-chinh.rss",
        "VnEconomy - Chung Khoan": "https://vneconomy.vn/chung-khoan.rss",
        "VnEconomy - BDS": "https://vneconomy.vn/bat-dong-san.rss",
        "VnEconomy - The Gioi": "https://vneconomy.vn/the-gioi.rss",
    })

    # Polling intervals (seconds)
    rss_poll_interval: int = int(os.getenv("RSS_POLL_INTERVAL", "120"))
    twitter_poll_interval: int = int(os.getenv("TWITTER_POLL_INTERVAL", "60"))
    facebook_poll_interval: int = int(os.getenv("FACEBOOK_POLL_INTERVAL", "180"))

    # Database
    db_path: str = os.getenv("DB_PATH", "news_bot.db")

    # Summarization language
    summary_language: str = os.getenv("SUMMARY_LANGUAGE", "vi")

    def get_chat_id(self, category: str) -> str:
        return {
            CATEGORY_VN_STOCK: self.telegram_chat_vn_stock,
            CATEGORY_WORLD_FINANCE: self.telegram_chat_world_finance,
            CATEGORY_CRYPTO: self.telegram_chat_crypto,
            CATEGORY_GOLD: self.telegram_chat_gold,
            CATEGORY_COMMODITY: self.telegram_chat_commodity,
        }.get(category, "")


config = Config()
