# News Summary Bot

Bot tu dong thu thap, tom tat va gui tin tuc tai chinh qua Telegram.

## Tinh nang

- **Thu thap tin tuc real-time** tu 120+ nguon RSS (Bloomberg, Reuters, CNBC, CafeF, VnExpress...)
- **X/Twitter** - theo doi 50+ tai khoan tai chinh lon
- **Facebook** - theo doi cac fanpage tin tuc
- **Tom tat bang AI** (OpenAI GPT hoac Anthropic Claude) - tom tat tieng Viet
- **Gui qua Telegram** - nhan tin ngay khi co
- **Chong trung lap** - SQLite database theo doi tin da gui
- **Phan loai tin tuc** - Vi mo, Chung khoan, Tien te, Hang hoa, Doanh nghiep

## Chi phi van hanh

> Chi tiet: [COST_ESTIMATION.md](COST_ESTIMATION.md)

| Kich ban | AI Model | Server | Chi phi/thang |
|----------|----------|--------|---------------|
| **Mien phi (GitHub Actions)** | claude-haiku-4-5 | GitHub Actions | **~$11** (chi AI) |
| **Tiet kiem** | gpt-4o-mini | GitHub Actions | **~$6** (chi AI) |
| **VPS** | claude-haiku-4-5 | VPS $5 | ~$16 |

- Telegram, Facebook, RSS: **Mien phi**
- Twitter Free tier: du cho 50+ accounts
- Server: **$0** (GitHub Actions) hoac $5-10 (VPS)
- AI: $6 - $11/thang (1,000-1,500 tin/ngay)

## Cai dat

### 1. Clone va cai dependencies

```bash
pip install -r requirements.txt
```

### 2. Tao Telegram Bot

1. Mo Telegram, tim `@BotFather`
2. Gui `/newbot` va lam theo huong dan
3. Luu lai **Bot Token**
4. Tao group/channel, them bot vao, lay **Chat ID**
   - Gui tin nhan trong group
   - Truy cap: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Tim `chat.id` trong response

### 3. Cau hinh

```bash
cp .env.example .env
# Chinh sua file .env voi cac credentials cua ban
```

### 4. Chay bot

**Cach 1: GitHub Actions (khuyen nghi - mien phi server)**

1. Push code len GitHub
2. Vao repo -> Settings -> Secrets and variables -> Actions
3. Them cac secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `ANTHROPIC_API_KEY`
   - `TWITTER_BEARER_TOKEN` (tuy chon)
4. Vao tab Actions -> bat workflow "News Summary Bot"
5. Bot se tu dong chay moi 5 phut

**Cach 2: Chay local / VPS**

```bash
# Chay lien tuc
python -m news_bot.main

# Chay 1 lan (test)
python -m news_bot.main --once

# Docker
docker compose up -d
```

## Cau hinh API Keys

| Service | Bat buoc | Huong dan |
|---------|----------|-----------|
| Telegram Bot | Bat buoc | Tao bot qua @BotFather |
| OpenAI API | Khuyen nghi | https://platform.openai.com/api-keys |
| Anthropic API | Thay the | https://console.anthropic.com/ |
| Twitter API | Tuy chon | https://developer.twitter.com/ |
| Facebook API | Tuy chon | https://developers.facebook.com/ |

## Nguon tin (120+ feeds)

### Quoc te (70+ feeds)
- **Hang tin**: Reuters, AP, AFP
- **My**: Bloomberg, CNBC, WSJ, Financial Times, MarketWatch, Yahoo Finance, The Economist, Forbes, Business Insider, Barrons
- **Forex/Trading**: FX Street, Forex Factory, DailyFX, Forex Live, Trading Economics
- **Hang hoa**: OilPrice, Mining.com, Rigzone, Kitco, Platts
- **Crypto**: CoinDesk, CoinTelegraph, The Block, Decrypt, Bitcoin Magazine
- **NHTW**: Federal Reserve, ECB, IMF, World Bank, BIS
- **Chau Au**: Reuters UK, City AM, Les Echos, Handelsblatt, Euronews
- **Chau A**: Nikkei Asia, SCMP, CNA, Straits Times, Bangkok Post, Jakarta Post, Korea Herald, Economic Times India, China Daily, Asia Times
- **Trung Dong**: Al Jazeera, Gulf News, Arab News
- **Phan tich**: Seeking Alpha, Zero Hedge, Wolf Street, Calculated Risk

### Viet Nam (50+ feeds)
- **VnExpress**: Kinh Doanh, The Gioi, Chung Khoan, BDS, Vi Mo, Tai Chinh
- **CafeF**: Trang Chu, Chung Khoan, Vi Mo, TCQT, Doanh Nghiep, BDS, Ngan Hang, Hang Hoa, Vang, Tien Te
- **VietStock**: Tai Chinh, TTCK, Doanh Nghiep
- **Khac**: Thanh Nien, Tuoi Tre, Dan Tri, VTV, TBKTSG, BizLive, Bao Dau Tu, NDH, VnEconomy, Tin Nhanh CK, SBV

### X/Twitter (50+ accounts)
Reuters, Bloomberg, CNBC, WSJ, FT, MarketWatch, Yahoo Finance, Seeking Alpha, Zero Hedge, Federal Reserve, ECB, CoinDesk, Nikkei Asia, SCMP, MacroAlf, unusual_whales, DeItaone...

## Kien truc

```
news_bot/
|-- collectors/
|   |-- rss.py          # Thu thap tu 120+ RSS feeds
|   |-- twitter.py      # Thu thap tu X/Twitter API v2
|   |-- facebook.py     # Thu thap tu Facebook Graph API
|-- summarizer.py       # Tom tat tin bang AI (OpenAI/Anthropic)
|-- telegram_bot.py     # Gui tin qua Telegram Bot API
|-- database.py         # SQLite - chong trung lap
|-- config.py           # Cau hinh tu .env
|-- main.py             # Orchestrator chinh
```
