"""
Cache — SQLite local cache for OHLCV data.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class DataCache:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv_cache (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                fetched_at TEXT,
                PRIMARY KEY (symbol, date)
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_cache (
                symbol TEXT PRIMARY KEY,
                data TEXT,
                fetched_at TEXT
            )
        """)
        self.conn.commit()

    def get_ohlcv(self, symbol: str, expiry_hours: int = 6) -> pd.DataFrame | None:
        """Get cached OHLCV data if fresh enough."""
        cutoff = (datetime.now() - timedelta(hours=expiry_hours)).isoformat()
        rows = self.conn.execute(
            "SELECT date, open, high, low, close, volume FROM ohlcv_cache "
            "WHERE symbol = ? AND fetched_at > ? ORDER BY date",
            (symbol, cutoff)
        ).fetchall()
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        return df

    def store_ohlcv(self, symbol: str, df: pd.DataFrame):
        """Store OHLCV data into cache."""
        now = datetime.now().isoformat()
        records = []
        for date, row in df.iterrows():
            records.append((
                symbol, str(date.date()),
                float(row["Open"]), float(row["High"]),
                float(row["Low"]), float(row["Close"]),
                float(row["Volume"]), now
            ))
        self.conn.executemany(
            "INSERT OR REPLACE INTO ohlcv_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            records
        )
        self.conn.commit()

    def get_fundamentals(self, symbol: str, expiry_hours: int = 24) -> dict | None:
        """Get cached fundamental data if fresh enough."""
        cutoff = (datetime.now() - timedelta(hours=expiry_hours)).isoformat()
        row = self.conn.execute(
            "SELECT data FROM fundamental_cache WHERE symbol = ? AND fetched_at > ?",
            (symbol, cutoff)
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None

    def store_fundamentals(self, symbol: str, data: dict):
        """Store fundamental data into cache."""
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT OR REPLACE INTO fundamental_cache VALUES (?, ?, ?)",
            (symbol, json.dumps(data, default=str), now)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
