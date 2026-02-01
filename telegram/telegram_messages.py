import pandas as pd
from datetime import datetime
import requests


TOKEN =''
CHAT_ID = 123


def generate_hourly_summary():
    df = pd.read_csv("logs/live_trading.csv")

    last_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    df_hour = df[df["timestamp"] >= last_hour.strftime("%Y-%m-%d %H:%M:%S")]

    trades_opened = df_hour[df_hour["event"] == "OPEN_TRADE"]
    blocked = df_hour[df_hour["event"] == "TRADE_BLOCKED_MARGIN"]
    no_trades = df_hour[df_hour["event"].str.startswith("NO_TRADE")]

    summary = (
        f"📊 *Hourly Trading Summary*\n"
        f"Time: {last_hour}\n\n"
        f"Opened trades: {len(trades_opened)}\n"
        f"Blocked (margin): {len(blocked)}\n"
        f"No-trade signals: {len(no_trades)}\n"
    )

    return summary


def send_telegram(msg):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })
