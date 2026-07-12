from __future__ import annotations


UNIVERSES: dict[str, list[str]] = {
    "majors": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"],
    "solana": ["SOL/USDT", "JUP/USDT", "JTO/USDT", "BONK/USDT", "WIF/USDT", "PYTH/USDT"],
    "ai": ["FET/USDT", "TAO/USDT", "RENDER/USDT", "NEAR/USDT", "ARKM/USDT"],
    "defi": ["UNI/USDT", "AAVE/USDT", "MKR/USDT", "LDO/USDT", "CRV/USDT"],
    "hybrid": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XAU/USDT", "TSLA/USDT", "NVDA/USDT"],
}


def resolve_universe(name_or_symbols: list[str]) -> list[str]:
    if not name_or_symbols:
        return UNIVERSES["majors"]
    if len(name_or_symbols) == 1 and name_or_symbols[0].lower() in UNIVERSES:
        return UNIVERSES[name_or_symbols[0].lower()]
    return [item.upper() for item in name_or_symbols]


def universe_menu() -> str:
    return "\n".join(f"- {name}: {', '.join(symbols)}" for name, symbols in UNIVERSES.items())
