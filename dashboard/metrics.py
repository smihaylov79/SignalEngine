import numpy as np
import pandas as pd


def expectancy(profits):
    return np.mean(profits)


def payoff_ratio(avg_win, avg_loss):
    if avg_loss == 0:
        return None
    return abs(avg_win / avg_loss)


def profit_factor(gross_profit, gross_loss):
    if gross_loss == 0:
        return None
    return abs(gross_profit / gross_loss)


def add_confidence_bucket(df, bucket_size=0.05):
    df = df.copy()

    # Convert None → NaN
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")

    # Drop rows with missing confidence
    df = df.dropna(subset=["confidence"])

    bins = np.arange(0.5, 1.0001, bucket_size)
    labels = [f"{round(b,2)}-{round(b+bucket_size,2)}" for b in bins[:-1]]

    df["conf_bucket"] = pd.cut(df["confidence"], bins=bins, labels=labels, include_lowest=True)
    return df


def profit_by_confidence(df):
    return df.groupby("conf_bucket")["net_profit"].agg(["count", "sum", "mean"])


def profit_by_conf_and_direction(df):
    return df.groupby(["conf_bucket", "direction"])["net_profit"].agg(["count", "sum", "mean"])
