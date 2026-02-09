# News Summary Bot

Bot tự động thu thập, tóm tắt và gửi tin tức tài chính qua Telegram.

## Tính năng

- **Thu thập tin tức real-time** từ 30+ nguồn RSS (Bloomberg, Reuters, CNBC, CafeF, VnExpress...)
- **X/Twitter** - theo dõi các tài khoản tài chính lớn
- **Facebook** - theo dõi các fanpage tin tức
- **Tóm tắt bằng AI** (OpenAI GPT hoặc Anthropic Claude) - tóm tắt tiếng Việt
- **Gửi qua Telegram** - nhận tin ngay khi có
- **Chống trùng lặp** - SQLite database theo dõi tin đã gửi
- **Phân loại tin tức** - Vĩ mô, Chứng khoán, Tiền tệ, Hàng hóa, Doanh nghiệp

## Cài đặt

### 1. Clone và cài dependencies

```bash
pip install -r requirements.txt
```

### 2. Tạo Telegram Bot

1. Mở Telegram, tìm `@BotFather`
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu lại **Bot Token**
4. Tạo group/channel, thêm bot vào, lấy **Chat ID**
   - Gửi tin nhắn trong group
   - Truy cập: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Tìm `chat.id` trong response

### 3. Cấu hình

```bash
cp .env.example .env
# Chỉnh sửa file .env với các credentials của bạn
```

### 4. Chạy bot

```bash
# Chạy trực tiếp
python -m news_bot.main

# Hoặc dùng Docker
docker compose up -d
```

## Cấu hình API Keys

| Service | Bắt buộc | Hướng dẫn |
|---------|----------|-----------|
| Telegram Bot | ✅ Có | Tạo bot qua @BotFather |
| OpenAI API | ⚡ Khuyến nghị | https://platform.openai.com/api-keys |
| Anthropic API | 🔄 Thay thế | https://console.anthropic.com/ |
| Twitter API | ❌ Tùy chọn | https://developer.twitter.com/ |
| Facebook API | ❌ Tùy chọn | https://developers.facebook.com/ |

## Nguồn tin RSS

### Quốc tế
Reuters, Bloomberg, CNBC, WSJ, Financial Times, MarketWatch, Yahoo Finance, The Economist, Forbes, Business Insider, FX Street, Seeking Alpha, Zero Hedge, Nikkei Asia, SCMP

### Việt Nam
VnExpress, CafeF, VietStock, Thanh Niên, Tuổi Trẻ, Người Lao Động, Dân Trí, VTV, TBKTSG

## Kiến trúc

```
news_bot/
├── collectors/
│   ├── rss.py          # Thu thập từ RSS feeds
│   ├── twitter.py      # Thu thập từ X/Twitter API
│   └── facebook.py     # Thu thập từ Facebook Graph API
├── summarizer.py       # Tóm tắt tin bằng AI (OpenAI/Anthropic)
├── telegram_bot.py     # Gửi tin qua Telegram Bot API
├── database.py         # SQLite - chống trùng lặp
├── config.py           # Cấu hình từ .env
└── main.py             # Orchestrator chính
```
