# Binance Futures Testnet Trading Bot

A CLI-based trading bot built in Python for the Binance USDT-M Futures Testnet. Built as part of an application task.

---

## What it does

- Place MARKET and LIMIT orders on Binance Futures Testnet
- Supports BUY and SELL on any futures symbol (BTCUSDT, ETHUSDT, etc.)
- STOP_MARKET orders also supported as a bonus
- All inputs validated before hitting the API
- Logs every request and response to a file for debugging
- Clean error messages when things go wrong

---

## Project structure

```
files/
├── bot/
│   ├── __init__.py
│   ├── client.py          # handles all API calls and signing
│   ├── orders.py          # order logic and output formatting
│   ├── validators.py      # validates user inputs
│   └── logging_config.py  # sets up file + console logging
├── cli.py                 # entry point, all CLI commands
├── requirements.txt
└── README.md
```

---

## Setup

Make sure you have Python 3.10 or above.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Get your API keys from https://testnet.binancefuture.com (login with GitHub, go to API Key tab).

Create a `.env` file:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

Load it before running:
```bash
export $(cat .env | grep -v '^#' | xargs)
```

---

## How to run

**Ping the testnet (check connection):**
```bash
python cli.py ping
```

**Market BUY:**
```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.003
```

**Market SELL:**
```bash
python cli.py place-order --symbol BTCUSDT --side SELL --type MARKET --quantity 0.003
```

**Limit BUY:**
```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.003 --price 60000
```

**Limit SELL:**
```bash
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.003 --price 120000
```

**Stop-Market (bonus):**
```bash
python cli.py place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.003 --price 85000
```

**View account balances:**
```bash
python cli.py account
```

**List open orders:**
```bash
python cli.py open-orders --symbol BTCUSDT
```

**Cancel an order:**
```bash
python cli.py cancel-order --symbol BTCUSDT --order-id 12420376693
```

---

## Notes

- Minimum order value on testnet is $100 notional, so for BTC at ~$97k you need at least 0.002 quantity
- Credentials are loaded from environment variables, never hardcoded
- Logs go to `logs/trading_bot.log` automatically on first run
- The bot uses direct REST calls with `requests`, no third-party Binance SDK
- Default time-in-force for LIMIT orders is GTC (Good Till Cancelled)
- Tested on Python 3.13, macOS

---

## Assumptions

- Testnet account is in one-way mode (not hedge mode), so positionSide is set to BOTH
- User provides quantity that meets the symbol's precision rules
- API keys are for the futures testnet only, not mainnet
