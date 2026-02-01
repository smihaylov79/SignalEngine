import pandas as pd


class EquityCurve:

    @staticmethod
    def build(trades: pd.DataFrame, initial_balance: float = 2000):
        df = trades.sort_values("time")
        df["equity"] = initial_balance + df["profit"].cumsum()
        return df[["time", "equity"]]

    @staticmethod
    def max_drawdown(equity_curve: pd.DataFrame):
        curve = equity_curve["equity"]
        peak = curve.cummax()
        dd = (curve - peak)
        return dd.min()
