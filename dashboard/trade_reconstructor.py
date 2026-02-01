import pandas as pd
import re

class TradeReconstructor:

    @staticmethod
    def reconstruct(deals: pd.DataFrame) -> pd.DataFrame:
        df = deals.copy().sort_values("time")

        trades = []

        for pos_id, group in df.groupby("position_id"):
            group = group.sort_values("time")

            # Entry = first deal with entry == 1
            entry_deals = group[group["entry"] == 1]
            if entry_deals.empty:
                continue
            entry = entry_deals.iloc[0]

            # Exit = last deal with entry == 0
            exit_deals = group[group["entry"] == 0]
            if exit_deals.empty:
                continue
            exit_ = exit_deals.iloc[-1]

            # Extract confidence from entry comment
            conf = TradeReconstructor._extract_confidence(entry.get("comment", ""))

            # Build trade record
            trades.append({
                "position_id": pos_id,
                "symbol": entry["symbol"],
                "direction": "BUY" if entry["type"] == 0 else "SELL",
                "volume": entry["volume"],
                "entry_time": entry["time"],
                "entry_price": entry["price"],
                "exit_time": exit_["time"],
                "exit_price": exit_["price"],
                "profit": group["profit"].sum(),
                "commission": group["commission"].sum(),
                "swap": group["swap"].sum(),
                "net_profit": group["profit"].sum() + group["commission"].sum() + group["swap"].sum(),
                "confidence": conf,
                "duration_sec": (exit_["time"] - entry["time"]).total_seconds(),
                "exit_reason": exit_["comment"],
            })

        return pd.DataFrame(trades)

    @staticmethod
    def _extract_confidence(comment: str):
        match = re.search(r"conf:([0-9.]+)", comment)
        return float(match.group(1)) if match else None
