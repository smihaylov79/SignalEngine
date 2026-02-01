# dashboard/data_extraction.py

import datetime as dt
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List

import MetaTrader5 as mt5
import pandas as pd
from .paths import DB_PATH


TRADES_TABLE = "trades"


class TradeDataExtractor:
    @staticmethod
    def _ensure_mt5_initialized() -> None:
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize() failed, error code: {mt5.last_error()}")

    @staticmethod
    def _get_history_window(
        start: Optional[dt.datetime],
        end: Optional[dt.datetime],
    ) -> Tuple[dt.datetime, dt.datetime]:
        now = dt.datetime.now()
        if end is None:
            end = now
        if start is None:
            # default: last 7 days
            start = end - dt.timedelta(days=7)
        return start, end

    @staticmethod
    def _load_deals(start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
        deals = mt5.history_deals_get(start, end)
        if deals is None:
            raise RuntimeError(f"history_deals_get returned None, error: {mt5.last_error()}")
        if len(deals) == 0:
            raise RuntimeError("No deals in the specified period")

        df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        df.columns = [c.lower() for c in df.columns]
        return df

    @staticmethod
    def _load_orders(start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
        orders = mt5.history_orders_get(start, end)
        if orders is None:
            raise RuntimeError(f"history_orders_get returned None, error: {mt5.last_error()}")
        if len(orders) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(list(orders), columns=orders[0]._asdict().keys())
        df.columns = [c.lower() for c in df.columns]
        return df

    @staticmethod
    def _extract_confidence_from_comment(comment: str) -> Optional[float]:
        if not isinstance(comment, str):
            return None
        comment = comment.strip()
        if comment.startswith("conf:"):
            try:
                return float(comment.split("conf:")[1])
            except Exception:
                return None
        return None

    @staticmethod
    def _build_trades_from_deals(
        deals_df: pd.DataFrame,
        orders_df: pd.DataFrame,
    ) -> pd.DataFrame:
        # Map opening order -> confidence
        # For Admirals, opening market orders have comment like "conf:0.65"
        order_conf = {}
        if not orders_df.empty:
            for _, row in orders_df.iterrows():
                pos_id = row.get("position_id")
                if pd.isna(pos_id):
                    continue
                conf = TradeDataExtractor._extract_confidence_from_comment(row.get("comment", ""))
                if conf is not None:
                    order_conf[int(pos_id)] = conf

        trades: List[dict] = []

        # Group by position_id to reconstruct trades
        for position_id, group in deals_df.groupby("position_id"):
            group = group.sort_values("time")

            # entry = first deal, exit = last deal
            entry = group.iloc[0]
            exit_ = group.iloc[-1]

            # direction from entry deal type
            # DEAL_TYPE_BUY = 0, DEAL_TYPE_SELL = 1 in MT5
            deal_type = int(entry["type"])
            if deal_type == mt5.DEAL_TYPE_BUY:
                direction = "BUY"
            elif deal_type == mt5.DEAL_TYPE_SELL:
                direction = "SELL"
            else:
                # fallback: sign of volume
                direction = "BUY" if entry["volume"] > 0 else "SELL"

            entry_time = pd.to_datetime(entry["time"], unit="s")
            exit_time = pd.to_datetime(exit_["time"], unit="s")

            entry_price = float(entry["price"])
            exit_price = float(exit_["price"])

            volume = float(group["volume"].sum())  # usually 1 deal, but sum is safe
            profit = float(group["profit"].sum())
            commission = float(group["commission"].sum())
            swap = float(group["swap"].sum())
            net_profit = profit + commission + swap

            # confidence from opening order comment if available
            confidence = order_conf.get(int(position_id), None)

            # exit_reason: last deal comment or reason
            exit_comment = str(exit_.get("comment", "") or "").strip()
            if exit_comment:
                exit_reason = exit_comment
            else:
                exit_reason = str(exit_.get("reason", ""))

            duration_sec = (exit_time - entry_time).total_seconds()

            trades.append(
                {
                    "position_id": int(position_id),
                    "symbol": entry["symbol"],
                    "direction": direction,
                    "volume": volume,
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "profit": profit,
                    "commission": commission,
                    "swap": swap,
                    "net_profit": net_profit,
                    "confidence": confidence,
                    "duration_sec": duration_sec,
                    "exit_reason": exit_reason,
                }
            )

        trades_df = pd.DataFrame(trades)
        trades_df = trades_df.sort_values("entry_time").reset_index(drop=True)
        return trades_df

    @staticmethod
    def _store_to_sqlite(df: pd.DataFrame, db_path: Path = DB_PATH, table: str = TRADES_TABLE):
        conn = sqlite3.connect(str(db_path))
        try:
            df.to_sql(table, conn, if_exists="replace", index=False)
        finally:
            conn.close()

    @classmethod
    def from_mt5_history(
        cls,
        start: Optional[dt.datetime] = None,
        end: Optional[dt.datetime] = None,
        store_sqlite: bool = True,
    ) -> pd.DataFrame:
        cls._ensure_mt5_initialized()
        start, end = cls._get_history_window(start, end)

        deals_df = cls._load_deals(start, end)
        orders_df = cls._load_orders(start, end)

        trades_df = cls._build_trades_from_deals(deals_df, orders_df)

        if store_sqlite:
            cls._store_to_sqlite(trades_df)

        return trades_df
