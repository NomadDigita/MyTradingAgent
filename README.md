# MyTradingAgent

**Telegram-approved, risk-controlled trading automation scaffold for Bitget markets.**

MyTradingAgent is an open-source trading-agent foundation built around a clear principle:
automation should be powerful, but every live trade must remain auditable, risk-capped, and operator-controlled.

The project currently ships with a Python trading engine, Telegram command interface, Bitget exchange adapter,
paper-trading mode, optional Go/Rust/TypeScript components, and Render-ready deployment files.

> This repository is a professional engineering scaffold, not a promise of profitability.
> No trading system can guarantee a fixed win rate or risk-free performance.

---

## Table of contents

- [What this bot does](#what-this-bot-does)
- [Safety model](#safety-model)
- [Current architecture](#current-architecture)
- [Features](#features)
- [Supported markets](#supported-markets)
- [Telegram workflow](#telegram-workflow)
- [Quick start](#quick-start)
- [Environment configuration](#environment-configuration)
- [Environment drafts](#environment-drafts)
- [Render deployment](#render-deployment)
- [Project structure](#project-structure)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Security checklist](#security-checklist)
- [Trading disclaimer](#trading-disclaimer)

---

## What this bot does

MyTradingAgent is designed to:

- analyze market candles using a baseline multi-factor strategy;
- build trade plans only when a signal passes risk checks;
- send trade plans to Telegram for human approval;
- execute approved orders through an exchange adapter;
- default to paper trading until live mode is explicitly enabled;
- cap leverage at a hard maximum of `20x`;
- provide a clean foundation for future research, broker adapters, and strategy modules.

The current default strategy is intentionally simple and inspectable. It combines EMA trend crossover,
RSI momentum filtering, and ATR-based stop/take-profit planning. This is a baseline module meant to be
extended or replaced, not a finished alpha engine.

---

## Safety model

Live automated trading is high risk. This repo therefore starts from conservative defaults:

| Control | Default | Purpose |
| --- | ---: | --- |
| Paper trading | `TRADING_MODE=paper` | Prevents real orders during setup |
| Human approval | `APPROVAL_REQUIRED=true` | Requires Telegram approval before execution |
| Max leverage | `MAX_LEVERAGE=20` | Hard cap; code also clamps above-20 values |
| Per-trade notional cap | `MAX_NOTIONAL_PER_TRADE=100` | Limits maximum trade size |
| Daily loss cap | `MAX_DAILY_LOSS=50` | Blocks new plans after configured daily loss |
| Telegram whitelist | `TELEGRAM_ALLOWED_USER_IDS` | Rejects commands from unauthorized users |
| Secret isolation | `.env` only | No API keys should be committed |

Recommended production progression:

1. Run locally in paper mode.
2. Deploy to Render in paper mode.
3. Verify Telegram whitelist and command behavior.
4. Test small notional limits.
5. Enable Bitget sandbox if available.
6. Enable live mode only after reviewing logs and risk controls.

---

## Current architecture

```text
Telegram User
    |
    v
Telegram Bot Commands
    |
    v
Trading Engine
    |-- Market Data Adapter
    |-- Strategy / Signal Engine
    |-- Risk Engine
    |-- Approval Book
    |-- Execution Engine
    |
    v
Paper Exchange or Bitget Exchange
```

Core flow:

1. User sends `/scan BTC/USDT`.
2. Bot fetches OHLCV candles.
3. Strategy analyzes the market.
4. Risk engine builds or rejects a trade plan.
5. Bot sends a Telegram approval request.
6. User sends `/approve <id>`.
7. Execution engine submits the order to paper mode or Bitget live mode.

---

## Features

### Implemented

- Telegram command interface.
- Telegram user whitelist.
- Trade approval flow.
- Paper trading exchange.
- Bitget adapter using CCXT.
- Multi-factor baseline analysis engine.
- ATR-based stop-loss and take-profit planning.
- Dynamic leverage calculation.
- Hard `20x` leverage cap.
- Per-trade notional limit.
- Daily loss guard.
- SQLite trade-plan storage adapter.
- Supabase REST storage adapter scaffold.
- Render Docker deployment support.
- Health endpoint for deployment platforms.
- Optional Go leverage/risk microservice.
- Optional Rust EMA indicator CLI.
- Optional TypeScript trade-plan schema utility.
- Python unit tests.

### Intentionally not included by default

- Guaranteed-profit logic.
- Hidden or unauditable execution.
- Live mode without explicit configuration.
- Committed secrets.
- Bypassing Telegram approval in production defaults.

---

## Supported markets

The project is structured to support multiple market types:

- spot;
- futures;
- swaps/perpetuals;
- CFDs;
- stocks;
- other broker/exchange assets.

However, the active exchange adapter is currently Bitget via CCXT. Actual tradable markets are limited to
what Bitget exposes through the connected account and API. If an asset class is not available on Bitget,
the project needs a separate broker adapter for that market.

Examples:

| Market | Current status |
| --- | --- |
| Crypto spot | Supported if available on Bitget |
| Crypto perpetuals/swaps | Supported if available on Bitget |
| Crypto futures | Supported if available on Bitget |
| CFDs | Requires compatible broker/exchange adapter if not available on Bitget |
| US stocks | Requires compatible broker adapter if not available on Bitget |

---

## Telegram workflow

### Commands

| Command | Description |
| --- | --- |
| `/start` | Shows bot intro and command list |
| `/status` | Shows trading mode, approval mode, leverage cap, pending approvals |
| `/scan BTC/USDT` | Analyzes a symbol and creates a trade plan when actionable |
| `/pending` | Lists pending approval requests |
| `/approve <id>` | Approves and executes a pending trade plan |
| `/reject <id>` | Rejects a pending trade plan |

### Example approval message

```text
Trade approval required.
Approval ID: 8ac31f02bd
Symbol: BTC/USDT
Side: BUY
Amount: 0.001
Entry: 65000.000000
Notional: 65.00
Leverage: 3.5x
Stop loss: 63800.0
Take profit: 66800.0
Rationale:
- EMA12=...
- EMA26=...
- RSI14=...
- Bullish EMA crossover with acceptable momentum
Approve with /approve 8ac31f02bd
```

---

## Quick start

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m app.main
```

The bot will refuse Telegram commands unless `TELEGRAM_ALLOWED_USER_IDS` is configured.

---

## Environment configuration

All secrets and deployment settings should be provided through environment variables.
Do not commit `.env`, API keys, Telegram bot tokens, GitHub tokens, Supabase service keys, or broker credentials.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | empty | Telegram bot token from BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | Yes | empty | Comma-separated Telegram user IDs allowed to control the bot |
| `TRADING_MODE` | Yes | `paper` | `paper` or `live` |
| `APPROVAL_REQUIRED` | Yes | `true` | Requires Telegram approval before execution |
| `MAX_LEVERAGE` | Yes | `20` | Maximum leverage; code caps at `20` |
| `DEFAULT_RISK_PER_TRADE` | Yes | `0.005` | Fraction of account equity risked per plan |
| `MAX_NOTIONAL_PER_TRADE` | Yes | `100` | Maximum notional per trade |
| `MAX_DAILY_LOSS` | Yes | `50` | Daily loss guard |
| `BITGET_API_KEY` | Live only | empty | Bitget API key |
| `BITGET_API_SECRET` | Live only | empty | Bitget API secret |
| `BITGET_API_PASSWORD` | Live only | empty | Bitget API passphrase/password |
| `BITGET_SANDBOX` | Optional | `false` | Enables Bitget sandbox mode when supported |
| `DATABASE_URL` | Optional | `sqlite:///data/trading_agent.sqlite` | SQLite database URL |
| `SUPABASE_URL` | Optional | empty | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | empty | Supabase service role key; keep server-side only |
| `RISK_SERVICE_URL` | Optional | empty | Optional Go risk service base URL |
| `LOG_LEVEL` | Optional | `INFO` | Python logging level |

---

## Environment drafts

Use these as copy/paste starting points. Replace placeholders with your own values.

### Draft 1: safest local paper mode

```env
TELEGRAM_BOT_TOKEN=replace_with_new_test_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456789

TRADING_MODE=paper
APPROVAL_REQUIRED=true
MAX_LEVERAGE=3
DEFAULT_RISK_PER_TRADE=0.0025
MAX_NOTIONAL_PER_TRADE=25
MAX_DAILY_LOSS=25

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
RISK_SERVICE_URL=
LOG_LEVEL=INFO
```

### Draft 2: Render paper mode

```env
TELEGRAM_BOT_TOKEN=replace_with_render_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456789

TRADING_MODE=paper
APPROVAL_REQUIRED=true
MAX_LEVERAGE=5
DEFAULT_RISK_PER_TRADE=0.005
MAX_NOTIONAL_PER_TRADE=50
MAX_DAILY_LOSS=50

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
RISK_SERVICE_URL=
LOG_LEVEL=INFO
```

### Draft 3: Bitget sandbox mode

```env
TELEGRAM_BOT_TOKEN=replace_with_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456789

TRADING_MODE=live
APPROVAL_REQUIRED=true
MAX_LEVERAGE=5
DEFAULT_RISK_PER_TRADE=0.0025
MAX_NOTIONAL_PER_TRADE=25
MAX_DAILY_LOSS=25

BITGET_API_KEY=replace_with_sandbox_key
BITGET_API_SECRET=replace_with_sandbox_secret
BITGET_API_PASSWORD=replace_with_sandbox_passphrase
BITGET_SANDBOX=true

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
RISK_SERVICE_URL=
LOG_LEVEL=INFO
```

### Draft 4: highly restricted live mode

```env
TELEGRAM_BOT_TOKEN=replace_with_production_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456789

TRADING_MODE=live
APPROVAL_REQUIRED=true
MAX_LEVERAGE=10
DEFAULT_RISK_PER_TRADE=0.0025
MAX_NOTIONAL_PER_TRADE=50
MAX_DAILY_LOSS=50

BITGET_API_KEY=replace_with_live_key
BITGET_API_SECRET=replace_with_live_secret
BITGET_API_PASSWORD=replace_with_live_passphrase
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
RISK_SERVICE_URL=
LOG_LEVEL=INFO
```

### Draft 5: Supabase-backed deployment

```env
TELEGRAM_BOT_TOKEN=replace_with_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456789

TRADING_MODE=paper
APPROVAL_REQUIRED=true
MAX_LEVERAGE=5
DEFAULT_RISK_PER_TRADE=0.005
MAX_NOTIONAL_PER_TRADE=50
MAX_DAILY_LOSS=50

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=replace_with_service_role_key
RISK_SERVICE_URL=
LOG_LEVEL=INFO
```

Recommended starting point: **Draft 1** locally, then **Draft 2** on Render.

---

## Render deployment

This repository includes:

- `Dockerfile`
- `render.yaml`
- `/healthz` endpoint

Deployment steps:

1. Create a Render Web Service from the repository.
2. Select Docker deployment or use `render.yaml`.
3. Add environment variables from one of the drafts.
4. Start in `TRADING_MODE=paper`.
5. Confirm `/status` from Telegram.
6. Run `/scan BTC/USDT`.
7. Review generated trade plans.
8. Keep live trading disabled until paper behavior is verified.

Render notes:

- The health server binds to Render's `PORT` environment variable when present.
- Telegram polling runs inside the same process.
- Store secrets only in Render environment variables.

---

## Project structure

```text
app/
  config.py                 Environment configuration
  health.py                 Render-compatible health server
  main.py                   Application entrypoint
  telegram_bot.py           Telegram commands and approval workflow
  core/
    execution.py            Approval book and execution engine
    indicators.py           EMA, SMA, RSI, ATR helpers
    models.py               Trading models and enums
    risk.py                 Risk engine and leverage controls
    strategy.py             Baseline multi-factor strategy
  exchanges/
    base.py                 Exchange interface
    bitget.py               Bitget/CCXT live adapter
    paper.py                Paper-trading adapter
  storage/
    sqlite.py               SQLite trade-plan storage
    supabase.py             Supabase REST storage scaffold
  services/
    risk_go_client.py       Optional Go risk service client

services/
  risk-go/                  Optional Go leverage/risk microservice
  indicators-rust/          Optional Rust indicator CLI

tools/
  market_schema.ts          TypeScript trade-plan schema helper

deployment/
  render.md                 Render deployment checklist

tests/
  test_risk.py              Risk-engine unit tests
```

---

## Testing

Run Python tests:

```bash
python -m pytest
```

Run Python syntax compile check:

```bash
python -m compileall app tests
```

Optional Go service check:

```bash
cd services/risk-go
go test ./...
```

Optional Rust utility check:

```bash
cd services/indicators-rust
cargo test
```

---

## Roadmap

Potential next engineering milestones:

- exchange market discovery and symbol validation;
- real account balance and position dashboard;
- persistent order/approval history;
- backtesting engine;
- walk-forward strategy validation;
- portfolio-level exposure constraints;
- volatility regime detection;
- news and sentiment research adapters;
- performance analytics;
- broker adapters for non-Bitget assets;
- GitHub Actions CI workflow once a token with `workflow` scope is available.

---

## Security checklist

Before going live:

- Rotate any token that has ever been pasted into chat or logs.
- Use a dedicated Telegram bot token.
- Use a dedicated Bitget API key with the minimum permissions needed.
- Restrict Bitget API key by IP if your deployment allows a stable egress IP.
- Keep withdrawals disabled on exchange API keys.
- Keep `APPROVAL_REQUIRED=true`.
- Start with low `MAX_NOTIONAL_PER_TRADE`.
- Start with low `MAX_LEVERAGE`.
- Review bot logs after every approved order.
- Never commit `.env`.

---

## Trading disclaimer

Trading crypto, futures, CFDs, stocks, and leveraged products involves substantial risk.
This software is provided for engineering and research purposes. You are responsible for testing,
configuration, legal compliance, risk management, and all trading decisions made with the system.
