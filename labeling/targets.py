import pandas as pd

ENCODE_MAP = {-1: 0, 0: 1, 1: 2}
DECODE_MAP = {0: -1, 1: 0, 2: 1}


def add_directional_target(df: pd.DataFrame, horizon: int = 12) -> pd.DataFrame:
    df = df.copy()
    future_price = df["close"].shift(-horizon)
    df["future_ret"] = (future_price - df["close"]) / df["close"]

    # raw target
    df["target_raw"] = 0
    df.loc[df["future_ret"] > 0, "target_raw"] = 1
    df.loc[df["future_ret"] < 0, "target_raw"] = -1

    # encoded target for ML
    df["target"] = df["target_raw"].map(ENCODE_MAP)

    return df.dropna()
