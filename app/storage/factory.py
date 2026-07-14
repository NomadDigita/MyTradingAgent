from __future__ import annotations

from app.config import Settings
from app.storage.base import NullTradeStore, TradeStore
from app.storage.postgres import PostgresTradeStore
from app.storage.sqlite import SQLiteTradeStore
from app.storage.supabase import SupabaseTradeStore


def build_trade_store(settings: Settings) -> TradeStore:
    backend = settings.storage_backend
    if backend in {"none", "null", "off"}:
        return NullTradeStore()
    if backend == "sqlite":
        return SQLiteTradeStore(settings.database_url)
    if backend in {"supabase", "supabase_rest"}:
        if not settings.supabase_url or not settings.supabase_secret_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY are required for Supabase REST storage")
        return SupabaseTradeStore(settings.supabase_url, settings.supabase_secret_key)
    if backend in {"postgres", "supabase_postgres", "supabase_direct"}:
        if not settings.supabase_direct_database_url:
            raise RuntimeError(
                "SUPABASE_DIRECT_DATABASE_URL is required for Supabase direct Postgres storage"
            )
        return PostgresTradeStore(settings.supabase_direct_database_url)
    raise RuntimeError(
        "Unsupported STORAGE_BACKEND. Use sqlite, supabase_rest, supabase_postgres, or none."
    )
