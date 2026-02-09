# Chi phí vận hành News Summary Bot

## Tổng quan

| Hạng mục | Chi phí/tháng (USD) | Ghi chú |
|----------|---------------------|---------|
| **AI Summarization** | $5 - $30 | Tùy model & số lượng tin |
| **Server/VPS** | $5 - $20 | Hoặc miễn phí nếu chạy local |
| **Twitter API** | $0 - $100 | Free tier hoặc Basic |
| **Facebook API** | $0 | Miễn phí |
| **Telegram API** | $0 | Miễn phí |
| **RSS Feeds** | $0 | Miễn phí |
| **TỔNG** | **$5 - $150/tháng** | |

---

## 1. Chi phí AI Summarization (chi phí chính)

### Ước tính số lượng tin/ngày

| Nguồn | Số feeds/accounts | Tin mới/ngày (ước tính) |
|-------|-------------------|------------------------|
| RSS Feeds | 100+ feeds | ~800 - 1,500 tin |
| X/Twitter | 50+ accounts | ~200 - 500 tweets |
| Facebook | 10-20 pages | ~50 - 100 posts |
| **Tổng** | | **~1,000 - 2,000 tin/ngày** |

> Sau khi loại trùng lặp: **~800 - 1,500 tin mới/ngày**

### Token usage per article

| Component | Tokens |
|-----------|--------|
| System prompt | ~200 |
| Tiêu đề + nội dung tin | ~400 - 600 |
| **Input total** | **~600 - 800** |
| Output (tóm tắt) | ~100 - 200 |
| **Output total** | **~150** |

### Chi phí theo model (ước tính 1,000 tin/ngày)

#### OpenAI

| Model | Input ($/1M) | Output ($/1M) | Chi phí/tin | Chi phí/ngày | Chi phí/tháng |
|-------|-------------|---------------|-------------|-------------|---------------|
| **gpt-4o-mini** | $0.15 | $0.60 | $0.000195 | **$0.20** | **$5.85** |
| gpt-4o | $2.50 | $10.00 | $0.00325 | $3.25 | $97.50 |
| gpt-4-turbo | $10.00 | $30.00 | $0.0115 | $11.50 | $345.00 |

#### Anthropic

| Model | Input ($/1M) | Output ($/1M) | Chi phí/tin | Chi phí/ngày | Chi phí/tháng |
|-------|-------------|---------------|-------------|-------------|---------------|
| **claude-haiku-4-5** | $0.25 | $1.25 | $0.000363 | **$0.36** | **$10.88** |
| claude-sonnet-4-5 | $3.00 | $15.00 | $0.00435 | $4.35 | $130.50 |
| claude-opus-4-6 | $15.00 | $75.00 | $0.02175 | $21.75 | $652.50 |

### Khuyến nghị

| Kịch bản | Model | Chi phí/tháng |
|----------|-------|---------------|
| **Tiết kiệm nhất** | gpt-4o-mini | ~$6/tháng |
| **Cân bằng** | claude-haiku-4-5 | ~$11/tháng |
| **Chất lượng cao** | gpt-4o | ~$98/tháng |

---

## 2. Chi phí Server

| Phương án | Chi phí/tháng | Specs |
|-----------|---------------|-------|
| **Chạy local** (PC/laptop) | $0 | Luôn bật máy |
| **VPS giá rẻ** (Contabo, Vultr) | $5 - $10 | 1 vCPU, 1GB RAM |
| **Cloud** (AWS t3.micro, GCP e2-micro) | $0 - $10 | Free tier 12 tháng |
| **Docker trên NAS** | $0 | Nếu đã có NAS |
| **Railway/Render** | $0 - $7 | Free tier có giới hạn |

> Bot rất nhẹ, chỉ cần ~100MB RAM và minimal CPU.

---

## 3. Chi phí Twitter API

| Tier | Chi phí/tháng | Giới hạn | Ghi chú |
|------|---------------|----------|---------|
| **Free** | $0 | 500K tweets đọc/tháng, 1 app | Đủ cho bot |
| **Basic** | $100 | 10K tweets đọc/tháng (POST), 2 apps | Nếu cần search |
| **Pro** | $5,000 | 1M tweets đọc/tháng | Không cần thiết |

> **Khuyến nghị**: Free tier là đủ. Bot chỉ đọc ~15,000 tweets/tháng (50 accounts × 10 tweets × 30 ngày)

---

## 4. Chi phí Facebook Graph API

| Tier | Chi phí | Ghi chú |
|------|---------|---------|
| **Standard** | $0 | 200 calls/user/hour, đủ dùng |

---

## 5. Telegram Bot API

| Feature | Chi phí | Ghi chú |
|---------|---------|---------|
| **Bot API** | $0 | Không giới hạn tin nhắn |
| Rate limit | - | 30 msg/s cho groups, 1 msg/s cho users |

---

## Tổng hợp chi phí theo kịch bản

### Kịch bản 1: Tiết kiệm tối đa
| Hạng mục | Chi phí |
|----------|---------|
| AI: gpt-4o-mini | $6 |
| Server: local/free VPS | $0 |
| Twitter: Free tier | $0 |
| Facebook: Free | $0 |
| Telegram: Free | $0 |
| **TỔNG** | **~$6/tháng** |

### Kịch bản 2: Khuyến nghị
| Hạng mục | Chi phí |
|----------|---------|
| AI: claude-haiku-4-5 | $11 |
| Server: VPS giá rẻ | $5 |
| Twitter: Free tier | $0 |
| Facebook: Free | $0 |
| Telegram: Free | $0 |
| **TỔNG** | **~$16/tháng** |

### Kịch bản 3: Chất lượng cao
| Hạng mục | Chi phí |
|----------|---------|
| AI: gpt-4o | $98 |
| Server: Cloud | $10 |
| Twitter: Basic | $100 |
| Facebook: Free | $0 |
| Telegram: Free | $0 |
| **TỔNG** | **~$208/tháng** |

---

## Cách tối ưu chi phí

1. **Batch summarization**: Gom 5-10 tin cùng chủ đề, tóm tắt 1 lần → giảm 60-70% token
2. **Filter trước khi tóm tắt**: Lọc tin trùng lặp, tin không liên quan trước khi gọi AI
3. **Cache**: Lưu tóm tắt, không gọi AI lại cho tin đã xử lý
4. **Fallback**: Dùng fallback (không AI) cho tin ít quan trọng
5. **Rate limiting**: Giới hạn số tin tóm tắt/giờ để kiểm soát chi phí
