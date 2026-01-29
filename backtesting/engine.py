import numpy as np
import pandas as pd

from config import settings as cfg
# from live.mt5_client import get_mt5_rates
# from models.registry import generate_signals


def backtest_hedging(df, signals, conf,
                     sl_mult=cfg.SL_MULT,
                     tp_mult=cfg.TP_MULT,
                     initial_balance=cfg.INITIAL_BALANCE,
                     position_size=cfg.POSITION_SIZE,
                     conf_threshold=cfg.CONF_THRESHOLD,
                     atr_norm_threshold=cfg.ATR_NORM_THRESHOLD,
                     contr_size=1, lev=20, marg_limit=0.5):

    balance = initial_balance
    equity_curve = []
    open_trades = []
    trade_log = []
    used_margin = 0

    prices = df["close"].values
    highs = df["high"].values
    lows = df["low"].values
    atr = df["atr"].values
    atr_norm = (df["atr"] / df["close"]).values
    index = df.index

    for i in range(1, len(df)):
        price = prices[i]
        bar_high = highs[i]
        bar_low = lows[i]
        bar_time = index[i]

        # update open trades
        still_open = []
        for trade in open_trades:
            if trade["direction"] == 1:
                tp = trade["entry_price"] + tp_mult * trade["atr"]
                sl = trade["entry_price"] - sl_mult * trade["atr"]
                hit_tp = bar_high >= tp
                hit_sl = bar_low <= sl
                if hit_tp or hit_sl:
                    exit_price = tp if hit_tp else sl
                    pnl_points = exit_price - trade["entry_price"]
                    pnl = pnl_points * trade["size"]
                    balance += pnl
                    used_margin -= trade["margin"]
                    trade["exit_time"] = bar_time
                    trade["exit_price"] = exit_price
                    trade["pnl"] = pnl
                    trade["pnl_points"] = pnl_points
                    trade["holding_bars"] = i - trade["entry_index"]
                    trade_log.append(trade)
                else:
                    still_open.append(trade)
            else:
                tp = trade["entry_price"] - tp_mult * trade["atr"]
                sl = trade["entry_price"] + sl_mult * trade["atr"]
                hit_tp = bar_low <= tp
                hit_sl = bar_high >= sl
                if hit_tp or hit_sl:
                    exit_price = tp if hit_tp else sl
                    pnl_points = trade["entry_price"] - exit_price
                    pnl = pnl_points * trade["size"]
                    balance += pnl
                    used_margin -= trade["margin"]
                    trade["exit_time"] = bar_time
                    trade["exit_price"] = exit_price
                    trade["pnl"] = pnl
                    trade["pnl_points"] = pnl_points
                    trade["holding_bars"] = i - trade["entry_index"]
                    trade_log.append(trade)
                else:
                    still_open.append(trade)

        open_trades = still_open

        sig = signals[i]
        c = conf[i]
        vol = atr_norm[i]

        if vol < atr_norm_threshold:
            continue
        if c < conf_threshold:
            continue
        if sig != 0 and not np.isnan(atr[i]) and atr[i] > 0:
            trade_margin = (price * position_size * contr_size) / lev
            max_allowed_margin = balance * marg_limit
            if used_margin + trade_margin > max_allowed_margin:
                continue
            trade = {
                "entry_time": bar_time,
                "entry_index": i,
                "entry_price": price,
                "direction": sig,
                "size": position_size,
                "atr": atr[i],
                "confidence": c,
                "atr_norm": vol,
                "margin": trade_margin,
            }
            open_trades.append(trade)
            used_margin += trade_margin

        equity_curve.append({"time": bar_time, "equity": balance})

    equity_df = pd.DataFrame(equity_curve).set_index("time")
    trades_df = pd.DataFrame(trade_log)
    return balance, equity_df, trades_df

