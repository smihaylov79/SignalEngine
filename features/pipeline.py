import numpy as np
import pandas as pd
from .indicators import add_indicators


def build_features(df):
    df = df.copy()

    # basic returns
    df["ret_1"] = df["close"].pct_change()
    df["ret_5"] = df["close"].pct_change(5)
    df["ret_20"] = df["close"].pct_change(20)

    # candle structure
    df["range_norm"] = (df["high"] - df["low"]) / df["close"]
    df["body"] = (df["close"] - df["open"]) / df["open"]
    df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
    df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]

    # time features
    df["hour"] = df.index.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    df = add_indicators(df)
    df = df.dropna()

    return df
