import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from config import settings as cfg
from backtesting.engine import backtest_hedging
from live.mt5_client import get_mt5_rates
from models.registry import generate_signals
import MetaTrader5 as mt5
import pandas as pd


def run_backtest(model, df_raw, feature_cols):
    # Slice test window
    df_test = df_raw.loc[cfg.TEST_START : cfg.TEST_END].copy()

    # Generate signals on test data
    df_feat, signals, conf = generate_signals(model, df_test, feature_cols)

    # Run backtest
    final_balance, equity_df, trades_df = backtest_hedging(
        df_feat, signals, conf,
        sl_mult=cfg.SL_MULT,
        tp_mult=cfg.TP_MULT,
        initial_balance=cfg.INITIAL_BALANCE,
        position_size=cfg.POSITION_SIZE,
        conf_threshold=cfg.CONF_THRESHOLD,
        atr_norm_threshold=cfg.ATR_NORM_THRESHOLD,
        contr_size=1,
        lev=20,
        marg_limit=0.5
    )

    print("\n=== Out-of-Sample Backtest Summary ===")
    print(f"Initial balance: {cfg.INITIAL_BALANCE:.2f}")
    print(f"Final balance:   {final_balance:.2f}")
    print(f"Net PnL:         {final_balance - cfg.INITIAL_BALANCE:.2f} "
          f"({(final_balance / cfg.INITIAL_BALANCE - 1) * 100:.2f}%)")
    print(f"Total trades:    {len(trades_df)}")

    return equity_df, trades_df


def plot_equity(equity_df):
    plt.figure(figsize=(10, 5))
    equity_df["equity"].plot()
    plt.title("Equity Curve")
    plt.grid(True)
    plt.show()
