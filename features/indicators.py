from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands, AverageTrueRange


def add_indicators(df):
    df = df.copy()

    # Trend
    df["ema_fast"] = EMAIndicator(df["close"], window=10).ema_indicator()
    df["ema_slow"] = EMAIndicator(df["close"], window=50).ema_indicator()
    df["ema_slope"] = df["ema_fast"].diff()

    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    df["adx"] = ADXIndicator(df["high"], df["low"], df["close"]).adx()

    # Momentum
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    stoch = StochasticOscillator(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    df["williams_r"] = WilliamsRIndicator(df["high"], df["low"], df["close"]).williams_r()

    # Volatility
    atr = AverageTrueRange(df["high"], df["low"], df["close"])
    df["atr"] = atr.average_true_range()
    df["atr_norm"] = df["atr"] / df["close"]

    bb = BollingerBands(df["close"])
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()

    return df
