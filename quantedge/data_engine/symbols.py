"""
Symbols — Nifty 50 and Nifty 200 ticker lists.
"""

import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_symbols(filename: str) -> list[str]:
    """Load ticker symbols from a CSV file (one column: Symbol)."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Symbol file not found: {filepath}")
    symbols = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get("Symbol", "").strip()
            if symbol:
                symbols.append(symbol)
    return symbols


def get_nifty50() -> list[str]:
    return load_symbols("nifty50.csv")


def get_nifty200() -> list[str]:
    return load_symbols("nifty200.csv")
