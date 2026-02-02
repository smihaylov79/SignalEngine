from datetime import datetime
import MetaTrader5 as mt5
from config import settings as cfg

from execution.margin import get_long_short_margin
import csv
import os
from datetime import datetime


def log_event(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open("logs/live_trading.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_margin_state(prefix: str, direction: int, required_margin: float):
    account = mt5.account_info()
    long_used, short_used = get_long_short_margin()

    if account is None:
        log_event(f"{prefix} | ERROR: account_info() returned None")
        return

    equity = account.equity
    free_margin = account.margin_free
    margin_level = account.margin_level

    allowed = equity * cfg.MARGIN_LIMIT
    available_long = allowed - long_used
    available_short = allowed - short_used

    log_csv(
        "MARGIN_CHECK",
        direction="LONG" if direction == 1 else "SHORT",
        required_margin=required_margin,
        long_used=long_used,
        short_used=short_used,
        avail_long=available_long,
        avail_short=available_short,
        equity=equity,
        free_margin=free_margin,
        margin_level=margin_level,
    )

    # log_event(
    #     f"{prefix} | MARGIN CHECK | "
    #     f"dir={'LONG' if direction==1 else 'SHORT'} | "
    #     f"req={required_margin:.2f} | "
    #     f"long_used={long_used:.2f} | short_used={short_used:.2f} | "
    #     f"avail_long={available_long:.2f} | avail_short={available_short:.2f} | "
    #     f"equity={equity:.2f} | free_margin={free_margin:.2f} | "
    #     f"margin_level={margin_level:.2f}%"
    # )


TRADES_CSV_LOG_PATH = "logs/trades_log.csv"
LOW_LOGS_CSV_LOG_PATH = "logs/low_conf.csv"


def log_csv(event_type: str, **kwargs):
    """
    event_type: e.g. 'NO_TRADE', 'OPEN', 'BLOCKED', 'MARGIN', etc.
    kwargs: any additional fields you want to log
    """

    # Ensure directory exists
    os.makedirs(os.path.dirname(TRADES_CSV_LOG_PATH), exist_ok=True)

    # Prepare row
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    row = {"timestamp": ts, "event": event_type}
    row.update(kwargs)

    # Write header if file doesn't exist
    write_header = not os.path.exists(TRADES_CSV_LOG_PATH)

    with open(TRADES_CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def low_conf_log_csv(event_type: str, **kwargs):
    """
    event_type: e.g. 'NO_TRADE', 'OPEN', 'BLOCKED', 'MARGIN', etc.
    kwargs: any additional fields you want to log
    """

    # Ensure directory exists
    os.makedirs(os.path.dirname(LOW_LOGS_CSV_LOG_PATH), exist_ok=True)

    # Prepare row
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    row = {"timestamp": ts, "event": event_type}
    row.update(kwargs)

    # Write header if file doesn't exist
    write_header = not os.path.exists(LOW_LOGS_CSV_LOG_PATH)

    with open(LOW_LOGS_CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)