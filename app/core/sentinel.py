from __future__ import annotations

from statistics import mean, pstdev

from app.core.models import AlertLevel, Candle, SentinelAlert


class BlackSwanSentinel:
    """Statistical anomaly sentinel that can recommend operator halt."""

    def evaluate(self, symbol: str, candles: list[Candle]) -> SentinelAlert:
        if len(candles) < 40:
            return SentinelAlert(symbol, AlertLevel.WATCH, 0.25, False, ["insufficient anomaly baseline"])

        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        returns = [
            current / previous - 1
            for previous, current in zip(closes, closes[1:], strict=False)
            if previous
        ]
        recent = returns[-5:]
        baseline = returns[-35:-5]
        triggers: list[str] = []
        severity = 0.0

        baseline_vol = pstdev(baseline) if len(baseline) >= 2 else 0.0
        recent_vol = pstdev(recent) if len(recent) >= 2 else 0.0
        if baseline_vol and recent_vol > baseline_vol * 3:
            triggers.append("volatility explosion")
            severity += 0.35

        last_return = abs(returns[-1])
        if baseline_vol and last_return > baseline_vol * 5:
            triggers.append("single-candle shock")
            severity += 0.35
        elif last_return > 0.12:
            triggers.append("absolute single-candle shock")
            severity += 0.35

        volume_base = mean(volumes[-35:-5])
        if volume_base:
            volume_ratio = volumes[-1] / volume_base
            if volume_ratio > 4:
                triggers.append("volume spike")
                severity += 0.20
            elif volume_ratio < 0.15:
                triggers.append("volume collapse")
                severity += 0.20

        range_pct = (candles[-1].high - candles[-1].low) / max(candles[-1].close, 1e-9)
        if range_pct > 0.12:
            triggers.append("wide intrabar range")
            severity += 0.25

        severity = round(min(1.0, severity), 4)
        if severity >= 0.80:
            level = AlertLevel.CRITICAL
        elif severity >= 0.55:
            level = AlertLevel.WARNING
        elif severity >= 0.25:
            level = AlertLevel.WATCH
        else:
            level = AlertLevel.INFO
        return SentinelAlert(
            symbol=symbol,
            level=level,
            severity=severity,
            halt_recommended=severity >= 0.80,
            triggers=triggers or ["no anomaly trigger"],
        )
