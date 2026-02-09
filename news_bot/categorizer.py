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
    "vnindex", "vn-index", "vn index", "vn30", "hnx", "upcom", "hose", "hsx",
    "chung khoan", "chứng khoán", "cổ phiếu", "co phieu",
    "sàn chứng khoán", "san chung khoan",
    "vietcombank", "vietinbank", "techcombank", "vpbank", "bidv",
    "vingroup", "vinamilk", "hoa phat", "hoà phát", "masan", "novaland",
    "vàng sjc", "vang sjc",
    "nhnn", "ngan hang nha nuoc", "ngân hàng nhà nước",
]

# === MEDIUM-CONFIDENCE keywords (need 2+ matches or VN source) ===
_VN_STOCK_MEDIUM = [
    "viet nam", "việt nam", "vietnam",
    "ngan hang", "ngân hàng",
    "bat dong san", "bất động sản",
    "vi mo", "vĩ mô",
    "doanh nghiep", "doanh nghiệp",
    "thanh khoan", "thanh khoản",
    "fpt", "hpg", "msn", "mbb", "vcb", "tcb",
    "cafef", "vietstock",
]

_VN_STOCK_SOURCES = [
    "vnexpress", "cafef", "vietstock", "thanh nien", "tuoi tre",
    "nguoi lao dong", "dan tri", "vtv", "tbktsg", "bizlive",
    "bao dau tu", "ndh", "tctc", "tin nhanh ck", "sbv",
    "vneconomy",
]

_CRYPTO_STRONG = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "blockchain", "defi", "nft", "web3", "altcoin", "stablecoin",
    "binance", "coinbase", "solana", "xrp", "ripple",
    "dogecoin", "doge", "cardano", "polkadot",
    "tether", "usdt", "usdc",
    "halving", "memecoin", "meme coin",
    "bitcoin etf", "ethereum etf", "spot etf",
    "tiền điện tử", "tien dien tu", "tiền mã hóa",
]

_CRYPTO_SOURCES = [
    "coindesk", "cointelegraph", "the block", "decrypt",
    "bitcoin magazine", "wublockchain",
]

_GOLD_STRONG = [
    "gold price", "gia vang", "giá vàng",
    "xauusd", "xau/usd",
    "sjc", "pnj", "doji",
    "gold futures", "gold spot", "comex gold", "gold etf",
    "vàng 9999", "vang 9999", "vàng nhẫn", "vang nhan",
    "kim loại quý", "kim loai quy",
    "kitco", "bullion",
]

# "gold" alone needs 2+ context keywords to qualify
_GOLD_MEDIUM = [
    "gold", "vàng", "vang", "xau",
    "gold bar", "precious metal",
]

_GOLD_SOURCES = [
    "kitco",
]


def categorize(title: str, content: str, source: str) -> str:
    """Classify a news item into one of the 4 categories.

    Uses strong/medium keyword tiers to reduce miscategorization.
    Priority: VN Stock > Crypto > Gold > World Finance (fallback).
    """
    text = f"{title} {content}".lower()
    source_lower = source.lower()

    # --- Source-based routing (highest confidence) ---
    # VN sources -> VN Stock (unless clearly crypto/gold)
    for src in _VN_STOCK_SOURCES:
        if src in source_lower:
            if _matches_keywords(text, _CRYPTO_STRONG, threshold=2):
                return CATEGORY_CRYPTO
            if _matches_keywords(text, _GOLD_STRONG, threshold=1):
                return CATEGORY_GOLD
            return CATEGORY_VN_STOCK

    # Crypto sources -> Crypto
    for src in _CRYPTO_SOURCES:
        if src in source_lower:
            return CATEGORY_CRYPTO

    # Gold sources -> Gold
    for src in _GOLD_SOURCES:
        if src in source_lower:
            return CATEGORY_GOLD

    # --- Keyword-based routing ---
    # Strong keywords: 1 match is enough
    if _matches_keywords(text, _VN_STOCK_STRONG, threshold=1):
        # Double-check not primarily crypto/gold
        if _matches_keywords(text, _CRYPTO_STRONG, threshold=2):
            return CATEGORY_CRYPTO
        return CATEGORY_VN_STOCK

    if _matches_keywords(text, _CRYPTO_STRONG, threshold=1):
        return CATEGORY_CRYPTO

    if _matches_keywords(text, _GOLD_STRONG, threshold=1):
        return CATEGORY_GOLD

    # Medium keywords: need 2+ matches
    if _matches_keywords(text, _VN_STOCK_MEDIUM, threshold=2):
        return CATEGORY_VN_STOCK

    if _matches_keywords(text, _GOLD_MEDIUM, threshold=2):
        return CATEGORY_GOLD

    # --- Fallback: World Finance ---
    return CATEGORY_WORLD_FINANCE


def _matches_keywords(text: str, keywords: list[str], threshold: int = 1) -> bool:
    """Check if text matches at least `threshold` keywords."""
    count = 0
    for kw in keywords:
        if kw in text:
            count += 1
            if count >= threshold:
                return True
    return False
