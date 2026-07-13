# 🇦🇫 Afghanistan Purchasing Bot

A professional Telegram bot for China-to-Afghanistan purchasing agent business. Built with **aiogram 3**, supports multiple languages, automatic product extraction, shipping calculation, and a full admin panel.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Multi-Language** | English, Dari/Farsi, Pashto, Chinese (Simplified) |
| 🔗 **Product Extraction** | Auto-extract from Taobao, Pinduoduo, 1688 links |
| 💱 **Exchange Rates** | Live CNY→AFN conversion with manual fallback |
| 🚚 **Shipping Calculator** | Air/Sea/Land with weight-based tier pricing |
| 📅 **Delivery Estimates** | Automatic date range calculation |
| 📋 **Order Summary** | Full cost breakdown before confirmation |
| 💳 **Payment Instructions** | Office payment with address & contact info |
| 🔧 **Admin Panel** | Order management, rate updates, broadcast |
| 📦 **Order Tracking** | Status notifications to customers |
| 🎁 **Referral System** | Reward customers for bringing friends |
| 📸 **Photo Inspection** | Optional pre-shipping photo verification |

---

## 🏗️ Architecture

```
afghanistan_purchasing_bot/
├── bot/
│   ├── handlers/          # Telegram command & message handlers
│   │   ├── common.py      # Start, help, language selection
│   │   ├── orders.py      # Order flow (link → quantity → shipping → confirm)
│   │   ├── tracking.py    # Order tracking & referrals
│   │   └── admin.py       # Admin panel handlers
│   ├── services/          # Business logic layer
│   │   ├── exchange_service.py      # Currency conversion
│   │   ├── product_extractor.py     # Web scraping for products
│   │   ├── shipping_service.py      # Cost & delivery calculation
│   │   └── notification_service.py  # Customer notifications
│   ├── database/          # Data models & async queries
│   │   └── models.py      # SQLite schema + CRUD operations
│   ├── middlewares/       # Cross-cutting concerns
│   │   ├── i18n_middleware.py   # Language injection
│   │   └── admin_middleware.py  # Authorization check
│   ├── utils/             # Helpers
│   │   ├── i18n.py        # Translation dictionary (4 languages)
│   │   └── keyboards.py   # Inline & reply keyboard builders
│   └── locales/           # Placeholder for future JSON locale files
├── config/
│   └── settings.py        # Pydantic-based env config
├── data/                  # SQLite database storage
├── logs/                  # Application logs
├── main.py                # Entry point (polling/webhook)
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variable template
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- (Optional) VPS/Server for production deployment

### 2. Installation

```bash
# Clone or create project directory
mkdir afghanistan_purchasing_bot && cd afghanistan_purchasing_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

**Required variables:**
```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321  # Your Telegram ID(s)
```

### 4. Run (Development)

```bash
python main.py --polling
```

### 5. Run (Production with Webhook)

```bash
# Set in .env:
# ENVIRONMENT=production
# WEBHOOK_URL=https://yourdomain.com
# WEBHOOK_SECRET=random_secret_string

python main.py --webhook
```

---

## 📋 Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Register and show welcome | All |
| `/help` | Show help and instructions | All |
| `/track <order>` | Track order status | All |
| `/referral` | Get referral code | All |
| `/language` | Change language | All |
| `/admin` | Admin panel | Admins only |

---

## 🔄 Order Flow

```
User sends product link
        ↓
Bot extracts title, price, weight
        ↓
User selects quantity
        ↓
User chooses photo inspection (optional)
        ↓
User selects shipping method (Air/Sea/Land)
        ↓
Bot shows order summary with full cost breakdown
        ↓
User confirms order
        ↓
Bot generates order number + payment instructions
        ↓
User visits office to pay
        ↓
Admin marks as PAID → order processing begins
```

---

## 🔧 Admin Panel

Access via `/admin` (restricted to `ADMIN_IDS`).

**Features:**
- 📊 **Statistics** — Total users, orders, revenue
- 📋 **Orders** — View recent orders, search by number, update status
- 💱 **Exchange Rate** — Update CNY→AFN rate manually
- 🚚 **Shipping Rates** — Update Air/Sea/Land pricing
- 👥 **Users** — View user list (future)
- 📢 **Broadcast** — Send message to all users

**Status Updates:** When admin changes order status, customer receives automatic notification.

---

## 💱 Exchange Rates

The bot attempts to fetch live rates from:
- `api.exchangerate-api.com` (free, no key)
- `open.er-api.com` (backup)

If APIs fail, falls back to `FALLBACK_CNY_TO_AFN` from `.env`.

Admins can manually update rates via `/admin` → Exchange Rate.

---

## 🚚 Shipping Methods

| Method | Base Rate | Est. Days | Best For |
|--------|-----------|-----------|----------|
| ✈️ Air | ¥80/kg | 7 days | Urgent, lightweight |
| 🚢 Sea | ¥25/kg | 45 days | Heavy, bulk, non-urgent |
| 🚛 Land | ¥35/kg | 20 days | Balanced speed & cost |

**Volume Discounts:**
- 1-5kg: 10% off
- 5-10kg: 15% off
- 10-20kg: 20% off
- 20-50kg: 25% off
- 50kg+: 30% off

---

## 🎁 Referral System

1. User runs `/referral` to get unique code
2. Share link: `t.me/YourBot?start=REFCODE`
3. When referred friend places first order ≥ `REFERRAL_MIN_ORDER_AFN`, referrer earns `REFERRAL_REWARD_AFN`

---

## 📸 Photo Inspection

Optional service (¥15 per item):
- Admin takes photos of actual product before shipping
- Photos sent to customer for approval
- Helps verify quality and authenticity

---

## 🔒 Security

- Admin commands restricted by Telegram ID whitelist
- Webhook mode uses secret token verification
- Database uses parameterized queries (SQL injection safe)
- No sensitive data logged

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check `BOT_TOKEN` is correct |
| Product extraction fails | Site may block bots; user can enter manually |
| Database errors | Delete `data/bot.db` to reset (loses data!) |
| Webhook not working | Ensure HTTPS URL and port 8080 open |

---

## 📄 License

MIT License — Free for commercial use.

---

## 🤝 Support

For questions or customizations, contact:
- 📧 Email: your-email@example.com
- 📞 Phone: +93-XXX-XXXX-XXX
- 🏢 Office: Kabul, Afghanistan
