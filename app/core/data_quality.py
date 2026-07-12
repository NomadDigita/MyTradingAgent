from __future__ import annotations

from statistics import median

from app.core.models import Candle, DataQualityReport


class DataQualityGate:
    """Pre-analysis market-data gate.

    Institutions usually fail closed on questionable data. This gate scores candle
    integrity before any signal can be trusted.
    """

    def evaluate(self, symbol: str, candles: list[Candle]) -> DataQualityReport:
        issues: list[str] = []
        penalty = 0.0

        if len(candles) < 60:
            issues.append("insufficient candle history")
            penalty += 0.35

        timestamps = [c.timestamp for c in candles]
        if timestamps != sorted(timestamps):
            issues.append("timestamps are not sorted")
            penalty += 0.25
        if len(set(timestamps)) != len(timestamps):
            issues.append("duplicate timestamps detected")
            penalty += 0.20

        invalid_ohlc = [
            c
            for c in candles
            if min(c.open, c.high, c.low, c.close) <= 0
            or c.high < c.low
            or c.high < max(c.open, c.close)
            or c.low > min(c.open, c.close)
        ]
        if invalid_ohlc:
            issues.append(f"invalid OHLC rows: {len(invalid_ohlc)}")
            penalty += min(0.4, 0.05 * len(invalid_ohlc))

        zero_volume = sum(1 for c in candles if c.volume <= 0)
        if candles and zero_volume / len(candles) > 0.20:
            issues.append("more than 20% zero-volume candles")
            penalty += 0.15

        if len(candles) >= 5:
            intervals = [b.timestamp - a.timestamp for a, b in zip(candles, candles[1:], strict=False)]
            expected = median(intervals)
            if expected > 0:
                gap_count = sum(1 for item in intervals if item > expected * 1.8)
                if gap_count:
                    issues.append(f"timestamp gaps detected: {gap_count}")
                    penalty += min(0.25, gap_count / max(len(intervals), 1))

        extreme_returns = 0
        for previous, current in zip(candles, candles[1:], strict=False):
            if previous.close and abs(current.close / previous.close - 1) > 0.25:
                extreme_returns += 1
        if extreme_returns:
            issues.append(f"extreme candle-to-candle returns: {extreme_returns}")
            penalty += min(0.25, 0.05 * extreme_returns)

        score = round(max(0.0, 1.0 - penalty), 4)
        hard_fail = bool(invalid_ohlc) or timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps)
        return DataQualityReport(
            symbol=symbol,
            score=score,
            valid=score >= 0.70 and not hard_fail,
            issues=issues or ["data quality accepted"],
            candle_count=len(candles),
        )
