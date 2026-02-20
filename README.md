# 🤖 Binance Futures Testnet Trading Bot

A clean, production-quality Python CLI application for placing orders on the **Binance USDT-M Futures Testnet**.

---

## Features

| Feature | Details |
|---|---|
| **Order types** | MARKET, LIMIT, STOP_MARKET |
| **Sides** | BUY and SELL |
| **CLI** | `click`-powered with full `--help` on every command |
| **Validation** | Symbol, side, order type, quantity, price — validated before any API call |
| **Logging** | Rotating file log (`logs/trading_bot.log`) + console output |
| **Error handling** | API errors, network failures (with exponential-backoff retries), bad input |
| **Structure** | Clean separation: `client.py` (API layer) → `orders.py` (business logic) → `cli.py` (UI) |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, retry, HTTP)
│   ├── orders.py          # Order placement business logic + output formatting
│   ├── validators.py      # Input validation (all raise ValueError on failure)
│   └── logging_config.py  # Rotating file + console logger setup
├── logs/
│   └── trading_bot.log    # Auto-created on first run
├── cli.py                 # CLI entry point (Click)
├── .env.example           # Template for environment variables
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python **3.10+** (uses `str | float` union syntax)
- A Binance Futures Testnet account

### 2. Get Testnet Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Go to **API Key** tab → click **Generate** to create credentials
4. Copy your **API Key** and **Secret Key**

### 3. Install Dependencies

```bash
# Clone or unzip the project, then:
cd trading_bot

# (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install requirements
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
# Option A — export directly (terminal session only)
export BINANCE_API_KEY=your_api_key_here
export BINANCE_API_SECRET=your_api_secret_here

# Option B — use a .env file (recommended)
cp .env.example .env
# Edit .env and fill in your credentials

# Then load it:
source .env     # macOS/Linux
# On Windows, set them manually or use a tool like python-dotenv
```

> **Security**: Never commit your `.env` file or paste credentials into code.

---

## How to Run

All commands are run from inside the `trading_bot/` directory.

### Check Connectivity

```bash
python cli.py ping
```

### Place a MARKET BUY Order

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

### Place a MARKET SELL Order

```bash
python cli.py place-order \
  --symbol ETHUSDT \
  --side SELL \
  --type MARKET \
  --quantity 0.01
```

### Place a LIMIT BUY Order

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side BUY \
  --type LIMIT \
  --quantity 0.001 \
  --price 60000
```

### Place a LIMIT SELL Order

```bash
python cli.py place-order \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 70000
```

### Place a STOP_MARKET Order (Bonus)

```bash
# Triggers a MARKET order when price drops to 60000
python cli.py place-order \
  --symbol BTCUSDT \
  --side SELL \
  --type STOP_MARKET \
  --quantity 0.001 \
  --price 60000
```

### Show Account Balances

```bash
python cli.py account

# Include zero-balance assets
python cli.py account --show-all
```

### List Open Orders

```bash
# All symbols
python cli.py open-orders

# Specific symbol
python cli.py open-orders --symbol BTCUSDT
```

### Cancel an Order

```bash
python cli.py cancel-order --symbol BTCUSDT --order-id 3863571234
```

### Help

```bash
python cli.py --help
python cli.py place-order --help
```

---

## Example Output

```
═══════════════════════════════════════════════════════
  ORDER REQUEST SUMMARY
═══════════════════════════════════════════════════════
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Quantity    : 0.001
═══════════════════════════════════════════════════════

───────────────────────────────────────────────────────
  ORDER RESPONSE
───────────────────────────────────────────────────────
  Status       : ✅ SUCCESS
  Order ID     : 3863565051
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Order Status : FILLED
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 65432.10000
───────────────────────────────────────────────────────
```

---

## Logging

Logs are written to `logs/trading_bot.log` automatically on first run.

- **Console**: `INFO` level and above (clean, readable)
- **File**: `DEBUG` level and above (full request/response detail)
- **Rotation**: 5 MB per file, last 5 files kept

Log format:
```
2025-07-15 10:23:04 | INFO     | bot.orders | Order complete → id=3863565051 symbol=BTCUSDT ...
```

---

## Error Handling

| Error Type | Behaviour |
|---|---|
| Missing/invalid API credentials | Clear message on startup, exit code 1 |
| Invalid symbol / side / quantity | Validation error before any API call |
| Missing price for LIMIT order | Usage error with explanation |
| Binance API error (e.g. -2019) | Error code + message displayed and logged |
| Network timeout / connection error | Retried up to 3× with exponential back-off (1s, 2s, 4s) |
| Unexpected exception | Logged with full traceback, non-zero exit code |

---

## Assumptions

- The bot targets the **USDT-M Futures Testnet** exclusively (`https://testnet.binancefuture.com`)
- **Hedge mode is NOT enabled** on the testnet account (uses `positionSide=BOTH`)
- Quantity precision: the user is responsible for providing a quantity that meets the symbol's step-size filter (e.g. 0.001 BTC). Invalid precision will return a Binance API error `-1111`
- Credentials are loaded from environment variables (not hard-coded or stored in files)
- Python 3.10 or higher is required

---

## Requirements

```
requests>=2.31.0
click>=8.1.7
python-dotenv>=1.0.0
```

No third-party Binance SDK is used — all API calls are made via `requests` with manual HMAC-SHA256 signing, giving full visibility and control over every request.
