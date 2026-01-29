import pandas as pd


def load_csv(path):
    df = pd.read_csv(path, parse_dates=["time"], index_col="time")
    df = df.sort_index()
    return df
