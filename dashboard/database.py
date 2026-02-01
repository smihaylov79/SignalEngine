import sqlite3
import pandas as pd
from pathlib import Path
from .paths import DB_PATH


class TradeDatabase:

    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            position_id INTEGER,
            symbol TEXT,
            direction TEXT,
            volume REAL,
            entry_time TEXT,
            entry_price REAL,
            exit_time TEXT,
            exit_price REAL,
            profit REAL,
            commission REAL,
            swap REAL,
            net_profit REAL,
            confidence REAL,
            duration_sec REAL,
            exit_reason TEXT
        )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def save_trades(df: pd.DataFrame):
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("trades", conn, if_exists="append", index=False)
        conn.close()

    @staticmethod
    def load_trades() -> pd.DataFrame:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM trades", conn)
        conn.close()
        return df
