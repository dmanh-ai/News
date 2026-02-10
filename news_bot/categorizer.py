import logging
import re

from .config import (
    CATEGORY_VN_STOCK,
    CATEGORY_WORLD_FINANCE,
    CATEGORY_CRYPTO,
    CATEGORY_GOLD,
)

logger = logging.getLogger(__name__)

# === HIGH-CONFIDENCE keywords (1 match is enough) ===
_VN_STOCK_STRONG = [
    "vnindex", "vn-index", "vn index", "vn30", "hnx-index", "upcom",
    "hose", "hsx", "san hose", "san hnx",
    "chung khoan", "chứng khoán", "cổ phiếu", "co phieu",
    "sàn chứng khoán", "san chung khoan",
    "vietcombank", "vietinbank", "techcombank", "vpbank", "bidv",
    "vingroup", "vinamilk", "hoa phat", "hoà phát", "masan", "novaland",
    "vàng sjc", "vang sjc",
    "nhnn", "ngan hang nha nuoc", "ngân hàng nhà nước",
    "thi truong chung khoan", "thị trường chứng khoán",
]

# === MEDIUM-CONFIDENCE keywords (need 2+ matches or VN source) ===
_VN_STOCK_MEDIUM = [
    "viet nam", "việt nam", "vietnam",
    "ngan hang", "ngân hàng",
    "bat dong san", "bất động sản",
    "vi mo", "vĩ mô",
    "doanh nghiep", "doanh nghiệp",
    "thanh khoan", "thanh khoản",
    "cafef", "vietstock",
]

_VN_STOCK_SOURCES = [
    "vnexpress", "cafef", "vietstock", "thanh nien", "tuoi tre",
    "nguoi lao dong", "dan tri", "vtv", "tbktsg", "bizlive",
    "bao dau tu", "ndh", "tctc", "tin nhanh ck", "sbv",
    "vneconomy",
]

_CRYPTO_STRONG = [
    "bitcoin", "ethereum", "crypto", "cryptocurrency",
    "blockchain", "defi", "altcoin", "stablecoin",
    "binance", "coinbase", "solana", "ripple",
    "dogecoin", "cardano", "polkadot",
    "tether", "halving", "memecoin", "meme coin",
    "bitcoin etf", "ethereum etf", "spot etf",
    "tiền điện tử", "tien dien tu", "tiền mã hóa",
]

# Short crypto keywords that need word boundary matching
_CRYPTO_SHORT = ["btc", "eth", "xrp", "doge", "nft", "web3", "usdt", "usdc"]

_CRYPTO_SOURCES = [
    "coindesk", "cointelegraph", "the block", "decrypt",
    "bitcoin magazine", "wublockchain",
]

_GOLD_STRONG = [
    "gold price", "gia vang", "giá vàng",
    "xauusd", "xau/usd",
    "gold futures", "gold spot", "comex gold", "gold etf",
    "vàng 9999", "vang 9999", "vàng nhẫn", "vang nhan",
    "kim loại quý", "kim loai quy",
    "kitco", "bullion",
    "gia vang hom nay", "giá vàng hôm nay",
]

# These need 2+ matches together
_GOLD_MEDIUM = [
    "gold", "precious metal",
]

# Short gold keywords that need word boundary
_GOLD_SHORT = ["sjc", "pnj", "doji", "xau"]

_GOLD_SOURCES = [
    "kitco",
]


def _word_match(text: str, word: str) -> bool:
    """Match a short keyword with word boundaries to avoid false positives."""
    return bool(re.search(r'\b' + re.escape(word) + r'\b', text))


def _matches_keywords(text: str, keywords: list[str], threshold: int = 1) -> bool:
    """Check if text matches at least `threshold` keywords (substring match)."""
    count = 0
    for kw in keywords:
        if kw in text:
            count += 1
            if count >= threshold:
                return True
    return False


def _matches_short_keywords(text: str, keywords: list[str], threshold: int = 1) -> bool:
    """Check short keywords with word boundary matching."""
    count = 0
    for kw in keywords:
        if _word_match(text, kw):
            count += 1
            if count >= threshold:
                return True
    return False


def categorize(title: str, content: str, source: str) -> str:
    """Classify a news item into one of the 4 categories.

    Uses strong/medium keyword tiers + word boundary for short keywords.
    Priority: VN Stock > Crypto > Gold > World Finance (fallback).
    """
    text = f"{title} {content}".lower()
    source_lower = source.lower()

    # --- Source-based routing (highest confidence) ---
    for src in _VN_STOCK_SOURCES:
        if src in source_lower:
            # VN source but check if actually about crypto/gold
            if _is_crypto(text):
                return CATEGORY_CRYPTO
            if _is_gold(text):
                return CATEGORY_GOLD
            return CATEGORY_VN_STOCK

    for src in _CRYPTO_SOURCES:
        if src in source_lower:
            return CATEGORY_CRYPTO

    for src in _GOLD_SOURCES:
        if src in source_lower:
            return CATEGORY_GOLD

    # --- Keyword-based routing ---
    # VN Stock (strong)
    if _matches_keywords(text, _VN_STOCK_STRONG, threshold=1):
        if _is_crypto(text):
            return CATEGORY_CRYPTO
        return CATEGORY_VN_STOCK

    # Crypto
    if _is_crypto(text):
        return CATEGORY_CRYPTO

    # Gold
    if _is_gold(text):
        return CATEGORY_GOLD

    # VN Stock (medium - need 2+ matches)
    if _matches_keywords(text, _VN_STOCK_MEDIUM, threshold=2):
        return CATEGORY_VN_STOCK

    # --- Fallback: World Finance ---
    return CATEGORY_WORLD_FINANCE


def _is_crypto(text: str) -> bool:
    """Check if text is about crypto."""
    if _matches_keywords(text, _CRYPTO_STRONG, threshold=1):
        return True
    if _matches_short_keywords(text, _CRYPTO_SHORT, threshold=1):
        return True
    return False


def _is_gold(text: str) -> bool:
    """Check if text is about gold."""
    if _matches_keywords(text, _GOLD_STRONG, threshold=1):
        return True
    if _matches_short_keywords(text, _GOLD_SHORT, threshold=1):
        return True
    if _matches_keywords(text, _GOLD_MEDIUM, threshold=2):
        return True
    return False
