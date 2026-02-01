import pandas as pd


class Summaries:

    @staticmethod
    def daily(trades: pd.DataFrame):
        trades["date"] = trades["time"].dt.date
        return trades.groupby("date")["profit"].sum().reset_index()
