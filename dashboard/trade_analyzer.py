import pandas as pd


class TradeAnalyzer:

    def __init__(self, trades: pd.DataFrame):
        self.trades = trades.copy()

    def basic_stats(self):
        df = self.trades

        total_trades = len(df)
        wins = df[df.profit > 0]
        losses = df[df.profit <= 0]

        return {
            "total_trades": total_trades,
            "win_rate": len(wins) / total_trades if total_trades else 0,
            "gross_profit": wins.profit.sum(),
            "gross_loss": losses.profit.sum(),
            "net_profit": df.profit.sum(),
            "avg_win": wins.profit.mean() if len(wins) else 0,
            "avg_loss": losses.profit.mean() if len(losses) else 0,
            "expectancy": df.profit.mean(),
        }

    def durations(self):
        df = self.trades
        if "time" in df.columns and "time_close" in df.columns:
            df["duration_sec"] = (df.time_close - df.time).dt.total_seconds()
            return df["duration_sec"].describe()
        return None
