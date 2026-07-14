# Optional Go risk service on Render

The main Python bot already has a built-in risk engine. `RISK_SERVICE_URL` is optional.

Use this only if you also deploy `services/risk-go` as a separate Render Web Service.

## Deploy steps

1. Create a second Render Web Service.
2. Point it to the same repository.
3. Set the root directory to `services/risk-go`.
4. Use Docker deployment.
5. Render will build `services/risk-go/Dockerfile`.
6. Confirm the service health endpoint is green at `/healthz`.
7. Copy the risk service URL from the Render service dashboard.
8. Put that URL into the main bot service as:

```env
RISK_SERVICE_URL=https://your-risk-service-host
```

If Render provides an internal/private service URL for service-to-service traffic, use that instead of the public URL.

## When to leave it blank

Leave `RISK_SERVICE_URL=` blank if you are only deploying the Python Telegram bot. The bot will still run because the Python risk engine is built in.
