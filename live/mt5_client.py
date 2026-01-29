from datetime import datetime, timedelta

import MetaTrader5 as mt5
import pandas as pd

from config.settings import LOCAL_TZ


def init_mt5(login=None, password=None, server=None):
    if not mt5.initialize():
        raise RuntimeError("MT5 initialization failed")

    if login is not None and password is not None and server is not None:
        authorized = mt5.login(login=login, password=password, server=server)
        if not authorized:
            raise RuntimeError("MT5 login failed")
    print("MT5 initialized")


def get_mt5_rates(symbol: str, timeframe, start_date, end_date, days=None) -> pd.DataFrame:
    # init_mt5()
    # utc_to = datetime.utcnow()
    # utc_from = utc_to - timedelta(days=days)

    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }

    tf = timeframe_map.get(timeframe)
    if tf is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    # --- NEW LOGIC --- # If start_date and end_date are provided → use them
    if start_date is not None and end_date is not None:
        rates = mt5.copy_rates_range(symbol, tf, start_date, end_date)
    else:
        if days is None:
            raise ValueError("Either days or (start_date and end_date) must be provided.")
        utc_to = datetime.utcnow()
        utc_from = utc_to - timedelta(days=days)
        rates = mt5.copy_rates_range(symbol, tf, utc_from, utc_to)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Failed to load data for {symbol}: {mt5.last_error()}")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df.index = df.index.tz_localize('UTC').tz_convert(LOCAL_TZ)
    df = df[["open", "high", "low", "close"]]

    return df


def get_bars(symbol, timeframe, n=500):
    # TODO: implement MT5 copy_rates_from_pos
    pass


def place_order(symbol, direction, volume, sl, tp):
    # TODO: implement order_send
    pass
