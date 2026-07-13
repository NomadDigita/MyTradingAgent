# Render deployment checklist

Use the included `render.yaml` or create a Docker Web Service.

## Required environment variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`
- `TRADING_MODE=paper`

## Live trading variables

Only add these after paper mode has been tested:

- `TRADING_MODE=live`
- `BITGET_API_KEY`
- `BITGET_API_SECRET`
- `BITGET_API_PASSWORD`
- `BITGET_SANDBOX=false`

## Risk controls

- `APPROVAL_REQUIRED=true`
- `MAX_LEVERAGE=20`
- `DEFAULT_RISK_PER_TRADE=0.005`
- `MAX_NOTIONAL_PER_TRADE=100`
- `MAX_DAILY_LOSS=50`
- `MAX_OPEN_POSITIONS=3`
- `MAX_SYMBOL_NOTIONAL=150`
- `MAX_PORTFOLIO_NOTIONAL=300`
- `MIN_SIGNAL_CONFIDENCE=0.58`
- `REQUIRE_STOP_LOSS=true`
- `APPROVAL_EXPIRY_MINUTES=15`
- `DEFAULT_SCAN_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT`
- `AUDIT_LOG_PATH=logs/audit.jsonl`

## Supabase variables

These are optional. If you only want local SQLite persistence, leave them blank.

- Supabase **Project URL / API URL** -> `SUPABASE_URL`
- Supabase **Publishable key / anon key** -> `SUPABASE_PUBLISHABLE_KEY`
- Supabase **Secret key / service_role key** -> `SUPABASE_SECRET_KEY`
- Supabase **Direct connection string** -> `SUPABASE_DIRECT_DATABASE_URL`

The default `DATABASE_URL=sqlite:///data/trading_agent.sqlite` is for the app’s local SQLite storage. Do not paste the Supabase direct connection string into `DATABASE_URL` unless a Postgres persistence implementation is added.

`RISK_SERVICE_URL` is not from Supabase. It is only for the optional Go service in `services/risk-go`.

## Notes

Render needs a web process with a health endpoint. The bot runs Telegram polling and exposes `/healthz` on port `10000`.
