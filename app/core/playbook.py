from __future__ import annotations


class IncidentPlaybook:
    """Operational runbooks for live-trading incidents."""

    PLAYBOOKS: dict[str, list[str]] = {
        "black_swan": [
            "Activate /halt immediately.",
            "Stop approving pending trades.",
            "Check /sentinel on major symbols.",
            "Review exchange status and funding/liquidity conditions.",
            "Resume only after volatility and liquidity normalize.",
        ],
        "bad_data": [
            "Do not approve any plan from the affected symbol.",
            "Run /alpha SYMBOL to inspect data-quality notes.",
            "Compare candles against a second data source.",
            "Restart market-data adapter if repeated gaps appear.",
        ],
        "slippage": [
            "Reduce MAX_NOTIONAL_PER_TRADE.",
            "Prefer TWAP routes from /route.",
            "Avoid low-liquidity hours and symbols.",
            "Review fills before increasing size.",
        ],
        "live_enablement": [
            "Keep withdrawals disabled on exchange API keys.",
            "Keep APPROVAL_REQUIRED=true.",
            "Set low notional and leverage caps.",
            "Run paper mode and /backtest diagnostics first.",
            "Enable live mode only after operational review.",
        ],
    }

    def render(self, name: str) -> str:
        key = name.lower()
        if key not in self.PLAYBOOKS:
            return "Available playbooks:\n" + "\n".join(f"- {item}" for item in sorted(self.PLAYBOOKS))
        return f"Playbook: {key}\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(self.PLAYBOOKS[key], 1))
