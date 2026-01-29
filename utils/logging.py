from datetime import datetime


def log_event(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open("logs/live_trading.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
