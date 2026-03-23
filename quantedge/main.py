"""
QuantEdge — Main entry point.
Usage:
  python main.py              → Run screener in CLI mode
  python main.py --server     → Start FastAPI web server
  python main.py --stock TCS  → Analyze a single stock
"""

import argparse
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantedge.screener.engine import run_full_screen, get_top_picks, get_multibagger_candidates, screen_single
from quantedge.config import TOP_PICKS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("quantedge")


def print_results(results: list[dict]):
    """Print screener results to terminal."""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()

        table = Table(title="QuantEdge — Top Picks", border_style="dim", header_style="bold gold1")
        table.add_column("#", style="dim", width=3)
        table.add_column("Symbol", style="bold white")
        table.add_column("Score", justify="right")
        table.add_column("Tech", justify="right")
        table.add_column("Fund", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("RSI", justify="right")
        table.add_column("SL", justify="right", style="red")
        table.add_column("Target", justify="right", style="green")
        table.add_column("Sector")
        table.add_column("MB?", justify="center")

        for i, r in enumerate(results, 1):
            sc = r["composite_score"]
            color = "green" if sc >= 14 else "yellow" if sc >= 10 else "red"
            table.add_row(
                str(i),
                r["symbol"],
                f"[{color}]{sc:.1f}/20[/{color}]",
                f"{r['technical_score']:.1f}",
                f"{r['fundamental_score']:.1f}",
                f"₹{r['current_price']:.2f}",
                f"{r['rsi']:.1f}",
                f"₹{r['stop_loss']}",
                f"₹{r['target']}",
                r.get("sector", "N/A")[:15],
                "🚀" if r.get("is_multibagger") else "—",
            )
        console.print(table)

        # Multibagger section
        mbs = [r for r in results if r.get("is_multibagger")]
        if mbs:
            console.print(f"\n[bold gold1]🚀 Multibagger Candidates ({len(mbs)}):[/bold gold1]")
            for r in mbs:
                console.print(f"  [bold]{r['symbol']}[/bold] — Score: {r['composite_score']:.1f} | ROE: {r.get('roe', 'N/A')} | Rev Growth: {r.get('revenue_growth', 'N/A')}")

    except ImportError:
        # Fallback without rich
        print("\n" + "=" * 80)
        print("  QUANTEDGE — TOP PICKS")
        print("=" * 80)
        print(f"{'#':<3} {'Symbol':<12} {'Score':>7} {'Tech':>5} {'Fund':>5} {'Price':>10} {'RSI':>6} {'MB?':>4}")
        print("-" * 80)
        for i, r in enumerate(results, 1):
            mb = "🚀" if r.get("is_multibagger") else "—"
            print(f"{i:<3} {r['symbol']:<12} {r['composite_score']:>6.1f} {r['technical_score']:>5.1f} {r['fundamental_score']:>5.1f} ₹{r['current_price']:>8.2f} {r['rsi']:>5.1f} {mb:>4}")


def run_server():
    """Start the FastAPI web server."""
    try:
        import uvicorn
        logger.info("Starting QuantEdge server on http://localhost:8000")
        uvicorn.run(
            "quantedge.dashboard.api:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )
    except ImportError:
        logger.error("Install uvicorn: pip install uvicorn")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="QuantEdge Stock Screener")
    parser.add_argument("--server", action="store_true", help="Start web server")
    parser.add_argument("--stock", type=str, help="Analyze a single stock")
    parser.add_argument("--nifty200", action="store_true", help="Screen Nifty 200 (default: Nifty 50)")
    parser.add_argument("--top", type=int, default=TOP_PICKS, help="Number of top picks to show")
    args = parser.parse_args()

    if args.server:
        run_server()
        return

    if args.stock:
        symbol = args.stock.upper()
        logger.info(f"Analyzing {symbol}...")
        result = screen_single(symbol)
        if result:
            print_results([result])
        else:
            logger.error(f"No data found for {symbol}")
        return

    logger.info(f"Running QuantEdge screener on {'Nifty 200' if args.nifty200 else 'Nifty 50'}...")
    results = run_full_screen(use_nifty200=args.nifty200)
    top = get_top_picks(results, n=args.top, min_score=0)
    print_results(top)


if __name__ == "__main__":
    main()
