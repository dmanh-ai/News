import logging
import re

from .config import (
    CATEGORY_VN_STOCK,
    CATEGORY_WORLD_FINANCE,
    CATEGORY_CRYPTO,
    CATEGORY_GOLD,
)

logger = logging.getLogger(__name__)

# Keywords for each category (lowercase)
_VN_STOCK_KEYWORDS = [
    "vnindex", "vn-index", "vn index", "hnx", "upcom", "hose",
    "chung khoan", "chứng khoán", "co phieu", "cổ phiếu",
    "san chung khoan", "sàn chứng khoán",
    "vnexpress", "cafef", "vietstock", "vn30", "hsx",
    "thanh khoan", "thanh khoản", "margin",
    "doanh nghiep", "doanh nghiệp",
    "ngan hang", "ngân hàng", "sbv", "nhnn",
    "bat dong san", "bất động sản", "bds",
    "vi mo", "vĩ mô", "gdp", "cpi",
    "vingroup", "vin", "fpt", "hpg", "msn", "mbb", "vcb", "tcb",
    "bidv", "vietcombank", "vietinbank", "techcombank", "vpbank",
    "hoa phat", "hoà phát", "masan", "novaland", "vinamilk",
    "tp ho chi minh", "hà nội", "ha noi", "ho chi minh",
    "viet nam", "việt nam", "vietnam",
]

_VN_STOCK_SOURCES = [
    "vnexpress", "cafef", "vietstock", "thanh nien", "tuoi tre",
    "nguoi lao dong", "dan tri", "vtv", "tbktsg", "bizlive",
    "bao dau tu", "ndh", "tctc", "tin nhanh ck", "sbv",
    "vneconomy",
]

_CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "blockchain", "defi", "nft", "web3", "altcoin", "stablecoin",
    "binance", "coinbase", "solana", "sol", "xrp", "ripple",
    "dogecoin", "doge", "cardano", "ada", "polkadot", "dot",
    "avalanche", "avax", "polygon", "matic", "tether", "usdt",
    "usdc", "token", "mining", "halving", "memecoin", "meme coin",
    "sec crypto", "spot etf", "bitcoin etf", "ethereum etf",
    "tiền điện tử", "tien dien tu", "tiền mã hóa", "tien ma hoa",
]

_CRYPTO_SOURCES = [
    "coindesk", "cointelegraph", "the block", "decrypt",
    "bitcoin magazine", "wublockchain",
]

_GOLD_KEYWORDS = [
    "gold", "vàng", "vang", "xau", "xauusd", "xau/usd",
    "gold price", "gia vang", "giá vàng",
    "sjc", "pnj", "doji", "gold bar", "gold futures",
    "precious metal", "kim loại quý", "kim loai quy",
    "gold spot", "comex gold", "gold etf",
    "vang sjc", "vàng sjc", "vang 9999", "vàng 9999",
    "vang nhan", "vàng nhẫn",
    "kitco", "bullion",
]

_GOLD_SOURCES = [
    "kitco",
]


def categorize(title: str, content: str, source: str) -> str:
    """Classify a news item into one of the 4 categories.

    Priority: VN Stock > Crypto > Gold > World Finance (fallback).
    """
    text = f"{title} {content}".lower()
    source_lower = source.lower()

    # --- Vietnam Stock Market ---
    # Source-based (high confidence)
    for src in _VN_STOCK_SOURCES:
        if src in source_lower:
            # But check if it's actually about crypto or gold
            if _matches_keywords(text, _CRYPTO_KEYWORDS, threshold=2):
                return CATEGORY_CRYPTO
            if _matches_keywords(text, _GOLD_KEYWORDS, threshold=2):
                return CATEGORY_GOLD
            return CATEGORY_VN_STOCK

    # Keyword-based
    if _matches_keywords(text, _VN_STOCK_KEYWORDS, threshold=1):
        return CATEGORY_VN_STOCK

    # --- Crypto ---
    for src in _CRYPTO_SOURCES:
        if src in source_lower:
            return CATEGORY_CRYPTO

    if _matches_keywords(text, _CRYPTO_KEYWORDS, threshold=1):
        return CATEGORY_CRYPTO

    # --- Gold ---
    for src in _GOLD_SOURCES:
        if src in source_lower:
            return CATEGORY_GOLD

    if _matches_keywords(text, _GOLD_KEYWORDS, threshold=1):
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
