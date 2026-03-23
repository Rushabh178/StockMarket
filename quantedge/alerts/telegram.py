"""
Telegram Alert Bot — Send screener results to Telegram.
"""

import logging
import urllib.request
import urllib.parse
import json
import html

from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send_alert(message: str) -> bool:
    """Send a text message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def format_screener_alert(results: list[dict], top_n: int = 5) -> str:
    """Format top screener results as a Telegram message."""
    lines = ["<b>QuantEdge Daily Screener</b>\n"]
    for i, r in enumerate(results[:top_n], 1):
        mb = " MULTIBAGGER" if r.get("is_multibagger") else ""
        lines.append(
            f"<b>{i}. {r['symbol']}</b>{mb}\n"
            f"   Price: {r['current_price']} | Score: {r['composite_score']}/20\n"
            f"   Tech: {r['technical_score']}/10 | Fund: {r['fundamental_score']}/10\n"
            f"   SL: {r['stop_loss']} | Target: {r['target']}\n"
            f"   RSI: {r['rsi']} | P/E: {r.get('pe_ratio', 'N/A')}\n"
        )

        ai_brief = r.get("ai_brief")
        if ai_brief:
            lines.append(f"   <i>{html.escape(ai_brief)}</i>\n")

    return "\n".join(lines)


def send_screener_results(results: list[dict]) -> bool:
    """Send formatted screener results to Telegram."""
    message = format_screener_alert(results)
    return send_alert(message)
