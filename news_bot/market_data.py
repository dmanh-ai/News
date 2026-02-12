"""Fetch market data from dmanh-ai/vnstock repo for commodity reports."""

import csv
import io
import logging
from datetime import datetime, timezone, timedelta

import aiohttp

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

RAW_BASE = "https://raw.githubusercontent.com/dmanh-ai/vnstock/main/data"


async def _fetch_csv(session: aiohttp.ClientSession, url: str) -> list[dict]:
    """Fetch a CSV file and return as list of dicts."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                logger.warning("Failed to fetch %s: %d", url, resp.status)
                return []
            text = await resp.text()
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)
    except Exception as e:
        logger.error("Error fetching %s: %s", url, e)
        return []


async def fetch_gold_prices(session: aiohttp.ClientSession) -> str:
    """Fetch gold prices and format as table."""
    rows = await _fetch_csv(session, f"{RAW_BASE}/gold_prices.csv")
    if not rows:
        return ""

    lines = ["<b>GIA VANG SJC</b>"]
    seen = set()
    for r in rows:
        name = r.get("name", "").strip()
        branch = r.get("branch", "").strip()
        buy = r.get("buy_price", "0")
        sell = r.get("sell_price", "0")
        key = f"{name}|{branch}"
        if key in seen:
            continue
        seen.add(key)
        try:
            buy_m = float(buy) / 1_000_000
            sell_m = float(sell) / 1_000_000
            lines.append(f"  {name} ({branch}): Mua {buy_m:.1f}tr - Ban {sell_m:.1f}tr")
        except (ValueError, TypeError):
            continue

    return "\n".join(lines) if len(lines) > 1 else ""


async def fetch_exchange_rates(session: aiohttp.ClientSession) -> str:
    """Fetch exchange rates and format as table."""
    rows = await _fetch_csv(session, f"{RAW_BASE}/exchange_rates.csv")
    if not rows:
        return ""

    important = ["USD", "EUR", "JPY", "GBP", "CNY", "KRW", "SGD", "THB", "AUD"]
    lines = ["<b>TY GIA NGOAI TE (VND)</b>"]
    for r in rows:
        code = r.get("currency_code", "").strip()
        if code not in important:
            continue
        name = r.get("currency_name", "").strip()
        buy = r.get("buy_transfer", "").strip()
        sell = r.get("sell", "").strip()
        lines.append(f"  {code} ({name}): Mua {buy} - Ban {sell}")

    return "\n".join(lines) if len(lines) > 1 else ""


async def fetch_market_breadth(session: aiohttp.ClientSession) -> str:
    """Fetch market breadth from latest daily snapshot."""
    rows = await _fetch_csv(session, f"{RAW_BASE}/latest/market_breadth.csv")
    if not rows:
        return ""

    lines = ["<b>DO RONG THI TRUONG</b>"]
    for r in rows:
        exchange = r.get("exchange", "").strip()
        adv = r.get("advancing", "0")
        dec = r.get("declining", "0")
        unc = r.get("unchanged", "0")
        lines.append(f"  {exchange}: Tang {adv} | Giam {dec} | Dung {unc}")

    return "\n".join(lines) if len(lines) > 1 else ""


async def fetch_foreign_flow(session: aiohttp.ClientSession) -> str:
    """Fetch foreign investor flows."""
    rows = await _fetch_csv(session, f"{RAW_BASE}/latest/foreign_flow.csv")
    if not rows:
        return ""

    lines = ["<b>DONG VON NGOAI</b>"]
    for r in rows:
        exchange = r.get("exchange", "").strip()
        net_val = r.get("foreign_net_value", "0")
        try:
            net_b = float(net_val) / 1_000_000_000
            direction = "Mua rong" if net_b >= 0 else "Ban rong"
            lines.append(f"  {exchange}: {direction} {abs(net_b):.1f} ty VND")
        except (ValueError, TypeError):
            continue

    return "\n".join(lines) if len(lines) > 1 else ""


async def fetch_top_movers(session: aiohttp.ClientSession) -> str:
    """Fetch top gainers and losers."""
    gainers = await _fetch_csv(session, f"{RAW_BASE}/latest/top_gainers.csv")
    losers = await _fetch_csv(session, f"{RAW_BASE}/latest/top_losers.csv")

    lines = []
    if gainers:
        lines.append("<b>TOP TANG GIA</b>")
        for r in gainers[:5]:
            sym = r.get("symbol", "")
            pct = r.get("percent_change", "0")
            price = r.get("close_price", "0")
            lines.append(f"  {sym}: {price} ({pct}%)")

    if losers:
        lines.append("<b>TOP GIAM GIA</b>")
        for r in losers[:5]:
            sym = r.get("symbol", "")
            pct = r.get("percent_change", "0")
            price = r.get("close_price", "0")
            lines.append(f"  {sym}: {price} ({pct}%)")

    return "\n".join(lines)


async def fetch_index_summary(session: aiohttp.ClientSession) -> str:
    """Fetch latest index data (VNINDEX, VN30, HNX)."""
    indices = ["VNINDEX", "VN30", "HNXINDEX"]
    lines = ["<b>CHI SO THI TRUONG</b>"]

    for idx in indices:
        rows = await _fetch_csv(session, f"{RAW_BASE}/indices/{idx}.csv")
        if not rows:
            continue
        last = rows[-1]
        close = last.get("close", "")
        ret = last.get("daily_return", "")
        rsi = last.get("rsi_14", "")
        try:
            ret_pct = float(ret) * 100 if ret else 0
            rsi_val = float(rsi) if rsi else 0
            sign = "+" if ret_pct >= 0 else ""
            rsi_text = f" | RSI: {rsi_val:.0f}" if rsi_val > 0 else ""
            lines.append(f"  {idx}: {close} ({sign}{ret_pct:.2f}%){rsi_text}")
        except (ValueError, TypeError):
            lines.append(f"  {idx}: {close}")

    return "\n".join(lines) if len(lines) > 1 else ""


async def build_market_data_table() -> str:
    """Build complete market data table from vnstock repo."""
    async with aiohttp.ClientSession() as session:
        sections = []

        index_summary = await fetch_index_summary(session)
        if index_summary:
            sections.append(index_summary)

        gold = await fetch_gold_prices(session)
        if gold:
            sections.append(gold)

        fx = await fetch_exchange_rates(session)
        if fx:
            sections.append(fx)

        breadth = await fetch_market_breadth(session)
        if breadth:
            sections.append(breadth)

        foreign = await fetch_foreign_flow(session)
        if foreign:
            sections.append(foreign)

        movers = await fetch_top_movers(session)
        if movers:
            sections.append(movers)

    if not sections:
        return "Khong lay duoc du lieu thi truong."

    return "\n\n".join(sections)
