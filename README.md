# MyTradingAgent

Open-source Telegram-controlled trading agent scaffold for Bitget markets.

## Important safety notes

- There is no such thing as a guaranteed high win-rate trading bot.
- The default mode is **paper trading**.
- Live execution requires `TRADING_MODE=live`, exchange credentials, a whitelisted Telegram user, and approval.
- Leverage is capped by configuration and defaults to a hard maximum of `20x`.
- Bitget support is limited to markets exposed by Bitget/CCXT. CFDs and US stocks require separate broker adapters if Bitget does not expose them.

## Features

- Telegram approval flow before execution.
- Bitget adapter via CCXT.
- Paper broker for testing without real funds.
- Risk engine with max leverage, daily loss, per-trade risk, and notional caps.
- Simple multi-factor technical analysis engine.
- Optional Go risk-service and Rust indicator utility to keep the repo polyglot without making deployment fragile.
- Render-ready Docker deployment.

## Quick start

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m app.main
```

## Telegram commands

- `/start` — bot introduction.
- `/status` — mode, risk settings, pending approvals.
- `/scan BTC/USDT` — analyze a symbol and create an approval request if actionable.
- `/pending` — list pending trade approvals.
- `/approve <id>` — approve and execute a pending plan.
- `/reject <id>` — reject a pending plan.

## Render deployment

1. Create a Render Web Service from this repo.
2. Use the included `render.yaml` or Dockerfile.
3. Add environment variables from `.env.example` in Render.
4. Keep `TRADING_MODE=paper` until paper execution and logs are verified.

## Repository layout

```text
app/                    Python Telegram bot and trading engine
services/risk-go/        Optional Go risk microservice
services/indicators-rust/ Optional Rust indicator CLI
tools/                  Optional TypeScript utilities
tests/                  Unit tests
deployment/             Deployment notes
```
