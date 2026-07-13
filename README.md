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
- reject bad market data through a fail-closed data-quality gate;
- produce alpha confluence cards from independent transparent voters;
- produce transparent research reports with regime, volatility, confidence, and risk notes;
- rank multiple markets through a scanner workflow;
- run lightweight walk-forward backtests as sanity diagnostics;
- monitor statistical black-swan anomalies before trade planning;
- run portfolio VaR, correlation, slippage, and liquidity preflight checks;
- preview smart execution routes with defensive TWAP slicing;
- generate internal specialist-agent swarm debate reports;
- provide operational incident playbooks;
- build trade plans only when a signal passes risk checks;
- send trade plans to Telegram for human approval;
- execute approved orders through an exchange adapter;
- default to paper trading until live mode is explicitly enabled;
- cap leverage at a hard maximum of `20x`;
- enforce portfolio, symbol, and open-position exposure limits;
- keep an append-only JSONL audit trail for approvals, rejections, kill-switch events, and executions;
- compute a tamper-evident audit hash root;
- scan named market universes such as majors, Solana, AI, DeFi, and hybrid markets;
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
| Symbol exposure cap | `MAX_SYMBOL_NOTIONAL=250` | Limits concentration in one instrument |
| Portfolio exposure cap | `MAX_PORTFOLIO_NOTIONAL=500` | Limits aggregate notional exposure |
| Open-position cap | `MAX_OPEN_POSITIONS=5` | Limits portfolio complexity |
| Stop-loss requirement | `REQUIRE_STOP_LOSS=true` | Blocks plans without a stop |
| Approval expiry | `APPROVAL_EXPIRY_MINUTES=15` | Prevents stale approvals |
| Operator kill switch | `/halt` and `/resume` | Blocks new plans during incidents |
| Daily loss cap | `MAX_DAILY_LOSS=50` | Blocks new plans after configured daily loss |
| Telegram whitelist | `TELEGRAM_ALLOWED_USER_IDS` | Rejects commands from unauthorized users |
| Audit log | `AUDIT_LOG_PATH=logs/audit.jsonl` | Records sensitive decisions |
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
    |-- Data Quality Gate
    |-- Alpha Confluence Engine
    |-- Black-Swan Sentinel
    |-- Strategy / Signal Engine
    |-- Research / Backtest Diagnostics
    |-- Risk Engine
    |-- Compliance / VaR / Correlation / Slippage
    |-- Smart Order Router
    |-- Swarm Triage
    |-- Approval Book
    |-- Audit Hash Chain
    |-- Execution Engine
    |
    v
Paper Exchange or Bitget Exchange
```

Core flow:

1. User sends `/scan BTC/USDT`.
2. Bot fetches OHLCV candles.
3. Data-quality gate checks candle integrity.
4. Black-swan sentinel checks anomaly conditions.
5. Strategy analyzes the market.
6. Risk engine builds or rejects a trade plan.
7. Optional `/preflight` validates VaR, correlation, liquidity, slippage, data, and anomaly gates.
8. Optional `/route` previews market-impact-aware order slicing.
9. Bot sends a Telegram approval request.
10. User sends `/approve <id>`.
11. Execution engine submits the order to paper mode or Bitget live mode.

---

## Features

### Implemented

- Telegram command interface.
- Telegram user whitelist.
- Trade approval flow.
- Expiring approval IDs.
- Operator kill switch.
- Paper trading exchange.
- Bitget adapter using CCXT.
- Multi-factor baseline analysis engine.
- Fail-closed candle data-quality gate.
- Alpha confluence card with transparent voter breakdown.
- Institutional research report layer.
- Multi-symbol market scanner.
- Named universe scanner.
- Black-swan statistical sentinel with auto-halt recommendation.
- Lightweight walk-forward backtester.
- Portfolio VaR gate.
- Correlation concentration gate.
- Liquidity and slippage estimator.
- Smart execution router with TWAP slicing preview.
- Pre-trade compliance aggregator.
- In-process specialist-agent swarm triage.
- Operational incident playbooks.
- Portfolio exposure dashboard.
- ATR-based stop-loss and take-profit planning.
- Dynamic leverage calculation.
- Hard `20x` leverage cap.
- Per-trade notional limit.
- Symbol and portfolio notional limits.
- Open-position count limits.
- Daily loss guard.
- Stop-loss requirement gate.
- Append-only JSONL audit journal.
- Tamper-evident audit hash-chain root command.
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
| `/research BTC/USDT` | Produces an institutional-style research report |
| `/alpha BTC/USDT` | Produces an alpha confluence card with voter reasons |
| `/sentinel BTC/USDT` | Runs black-swan anomaly checks; can auto-halt on critical severity |
| `/backtest BTC/USDT` | Runs a lightweight walk-forward sanity backtest |
| `/preflight BTC/USDT` | Runs institutional pre-trade compliance checks |
| `/route BTC/USDT` | Previews a smart execution route for a generated plan |
| `/swarm BTC/USDT` | Runs an internal specialist-agent debate report |
| `/playbook` | Lists operational incident playbooks |
| `/playbook black_swan` | Shows a specific incident runbook |
| `/scan BTC/USDT` | Analyzes a symbol and creates a trade plan when actionable |
| `/scan_many BTC/USDT ETH/USDT SOL/USDT` | Ranks symbols by research score |
| `/scan_many solana` | Ranks a named universe |
| `/universe` | Lists named universes |
| `/audit_root` | Shows JSONL audit validity and tamper-evident hash root |
| `/portfolio` | Shows equity, gross exposure, net exposure, leverage, and positions |
| `/risk` | Shows active risk limits |
| `/pending` | Lists pending approval requests |
| `/approve <id>` | Approves and executes a pending trade plan |
| `/reject <id>` | Rejects a pending trade plan |
| `/halt` | Activates operator kill switch |
| `/resume` | Clears operator kill switch |

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
| `MAX_OPEN_POSITIONS` | Yes | `5` | Maximum open-position count |
| `MAX_SYMBOL_NOTIONAL` | Yes | `250` | Maximum notional concentration in one symbol |
| `MAX_PORTFOLIO_NOTIONAL` | Yes | `500` | Maximum aggregate open plus planned notional |
| `MIN_SIGNAL_CONFIDENCE` | Yes | `0.55` | Minimum signal confidence before planning |
| `REQUIRE_STOP_LOSS` | Yes | `true` | Rejects plans without a stop loss |
| `APPROVAL_EXPIRY_MINUTES` | Yes | `15` | Minutes before pending approvals expire |
| `DEFAULT_SCAN_SYMBOLS` | Optional | `BTC/USDT,ETH/USDT,SOL/USDT` | Default `/scan_many` universe |
| `BITGET_API_KEY` | Live only | empty | Bitget API key |
| `BITGET_API_SECRET` | Live only | empty | Bitget API secret |
| `BITGET_API_PASSWORD` | Live only | empty | Bitget API passphrase/password |
| `BITGET_SANDBOX` | Optional | `false` | Enables Bitget sandbox mode when supported |
| `DATABASE_URL` | Optional | `sqlite:///data/trading_agent.sqlite` | Local app DB URL. Keep SQLite unless a PostgreSQL persistence layer is wired |
| `SUPABASE_URL` | Optional | empty | Supabase Project URL / API URL |
| `SUPABASE_PUBLISHABLE_KEY` | Optional | empty | Supabase publishable/anon key; mainly for frontend clients |
| `SUPABASE_SECRET_KEY` | Optional | empty | Supabase secret/service-role key for server-side REST persistence |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | empty | Backward-compatible alias for `SUPABASE_SECRET_KEY` |
| `SUPABASE_DIRECT_DATABASE_URL` | Optional | empty | Supabase direct Postgres connection string; not the same as `DATABASE_URL` in the default bot |
| `RISK_SERVICE_URL` | Optional | empty | Optional Go risk service URL if `services/risk-go` is deployed separately |
| `AUDIT_LOG_PATH` | Optional | `logs/audit.jsonl` | Append-only local audit log |
| `LOG_LEVEL` | Optional | `INFO` | Python logging level |

### Supabase field mapping

Supabase has several different values that look similar. Use them like this:

| Supabase dashboard label | Put it in | Needed now? | Notes |
| --- | --- | --- | --- |
| Project URL / API URL | `SUPABASE_URL` | Optional | Looks like `https://your-project.supabase.co` |
| Publishable key / anon key | `SUPABASE_PUBLISHABLE_KEY` | Usually no | Mainly for browser/frontend clients |
| Secret key / service_role key | `SUPABASE_SECRET_KEY` | Yes, if using Supabase REST storage | Server-side only. Do not expose in frontend code |
| Direct connection string | `SUPABASE_DIRECT_DATABASE_URL` | Not by default | Direct Postgres URL. Kept separate from the default SQLite `DATABASE_URL` |

`RISK_SERVICE_URL` is unrelated to Supabase. Leave it blank unless you deploy the optional Go risk microservice in `services/risk-go`; then set it to that service’s internal URL.

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
MAX_OPEN_POSITIONS=2
MAX_SYMBOL_NOTIONAL=50
MAX_PORTFOLIO_NOTIONAL=100
MIN_SIGNAL_CONFIDENCE=0.60
REQUIRE_STOP_LOSS=true
APPROVAL_EXPIRY_MINUTES=10
DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DIRECT_DATABASE_URL=
RISK_SERVICE_URL=
AUDIT_LOG_PATH=logs/audit.jsonl
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
MAX_OPEN_POSITIONS=3
MAX_SYMBOL_NOTIONAL=150
MAX_PORTFOLIO_NOTIONAL=300
MIN_SIGNAL_CONFIDENCE=0.58
REQUIRE_STOP_LOSS=true
APPROVAL_EXPIRY_MINUTES=15
DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DIRECT_DATABASE_URL=
RISK_SERVICE_URL=
AUDIT_LOG_PATH=logs/audit.jsonl
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
MAX_OPEN_POSITIONS=2
MAX_SYMBOL_NOTIONAL=50
MAX_PORTFOLIO_NOTIONAL=100
MIN_SIGNAL_CONFIDENCE=0.60
REQUIRE_STOP_LOSS=true
APPROVAL_EXPIRY_MINUTES=10
DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

BITGET_API_KEY=replace_with_sandbox_key
BITGET_API_SECRET=replace_with_sandbox_secret
BITGET_API_PASSWORD=replace_with_sandbox_passphrase
BITGET_SANDBOX=true

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DIRECT_DATABASE_URL=
RISK_SERVICE_URL=
AUDIT_LOG_PATH=logs/audit.jsonl
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
MAX_OPEN_POSITIONS=3
MAX_SYMBOL_NOTIONAL=150
MAX_PORTFOLIO_NOTIONAL=300
MIN_SIGNAL_CONFIDENCE=0.60
REQUIRE_STOP_LOSS=true
APPROVAL_EXPIRY_MINUTES=10
DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

BITGET_API_KEY=replace_with_live_key
BITGET_API_SECRET=replace_with_live_secret
BITGET_API_PASSWORD=replace_with_live_passphrase
BITGET_SANDBOX=false

DATABASE_URL=sqlite:///data/trading_agent.sqlite
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DIRECT_DATABASE_URL=
RISK_SERVICE_URL=
AUDIT_LOG_PATH=logs/audit.jsonl
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
MAX_OPEN_POSITIONS=3
MAX_SYMBOL_NOTIONAL=150
MAX_PORTFOLIO_NOTIONAL=300
MIN_SIGNAL_CONFIDENCE=0.58
REQUIRE_STOP_LOSS=true
APPROVAL_EXPIRY_MINUTES=15
DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

BITGET_API_KEY=
BITGET_API_SECRET=
BITGET_API_PASSWORD=
BITGET_SANDBOX=false

DATABASE_URL=
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=replace_with_publishable_or_anon_key
SUPABASE_SECRET_KEY=replace_with_secret_or_service_role_key
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DIRECT_DATABASE_URL=postgresql://postgres.your-ref:password@aws-0-region.pooler.supabase.com:6543/postgres
RISK_SERVICE_URL=
AUDIT_LOG_PATH=logs/audit.jsonl
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
    alpha.py                Transparent alpha confluence engine
    attestation.py          Tamper-evident audit hash-chain root
    audit.py                Append-only JSONL audit journal
    backtest.py             Lightweight walk-forward backtesting diagnostics
    compliance.py           Aggregated pre-trade compliance gate
    correlation.py          Correlation and concentration risk helpers
    data_quality.py         Fail-closed candle integrity checks
    execution.py            Approval book and execution engine
    indicators.py           EMA, SMA, RSI, ATR helpers
    models.py               Trading models and enums
    order_router.py         Smart order-routing and slicing preview
    playbook.py             Operational incident playbooks
    portfolio.py            Portfolio exposure snapshot helpers
    research.py             Institutional research and regime scoring layer
    risk.py                 Risk engine and leverage controls
    scanner.py              Multi-symbol research scanner
    sentinel.py             Black-swan anomaly sentinel
    slippage.py             Liquidity and slippage estimator
    strategy.py             Baseline multi-factor strategy
    swarm.py                In-process specialist-agent debate reports
    universe.py             Named market universes
    var.py                  Portfolio VaR checks
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
  test_execution.py         Approval expiry tests
  test_institutional_layers.py Data quality, alpha, sentinel, attestation tests
  test_platform_layers.py   VaR, slippage, routing, compliance, swarm tests
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
- full portfolio backtesting engine with shared capital;
- walk-forward optimization and out-of-sample validation;
- correlation-aware portfolio exposure constraints;
- advanced volatility-regime model;
- event-driven risk daemon;
- VaR / expected shortfall research module;
- pre-trade slippage and liquidity checks;
- post-trade performance attribution;
- cryptographic Ed25519 signatures for audit batches;
- exchange websocket ingestion and order-book analytics;
- authenticated web control plane with read-only investor dashboard;
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
