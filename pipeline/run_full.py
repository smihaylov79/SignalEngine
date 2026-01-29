from config import settings as cfg
from features.pipeline import build_features
from labeling.targets import add_directional_target
from live.mt5_client import init_mt5, get_mt5_rates
from models.train import train_model
from models.registry import generate_signals
from backtesting.engine import backtest_hedging
from backtesting.reports import plot_equity
import pandas as pd
import json
import os


def run_full_pipeline(profile_name="baseline", use_best_params=False):
    print("=== SignalEngine: Full Pipeline ===")

    best_params = None
    if use_best_params:
        path = os.path.join("config", "best_params.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                best_params = json.load(f)
            print(f"Loaded optimized parameters for profile '{profile_name}'")
        else:
            print("No best_params.json found. Using defaults.")

    # Extract optimized parameters or fall back to defaults
    sl_mult = best_params["sl_mult"] if best_params else cfg.SL_MULT
    tp_mult = best_params["tp_mult"] if best_params else cfg.TP_MULT
    conf_threshold = best_params["conf_threshold"] if best_params else cfg.CONF_THRESHOLD
    atr_norm_threshold = best_params["atr_norm_threshold"] if best_params else cfg.ATR_NORM_THRESHOLD
    horizon = best_params["horizon"] if best_params else cfg.HORIZON

    model_params = None
    if best_params:
        model_params = {
            "max_depth": best_params["max_depth"],
            "learning_rate": best_params["learning_rate"],
            "n_estimators": best_params["n_estimators"],
            "subsample": best_params["subsample"],
            "colsample_bytree": best_params["colsample_bytree"],
            "min_child_weight": best_params["min_child_weight"],
            "gamma": best_params["gamma"],
        }

    # 1. Init MT5
    print("Initializing MT5...")
    init_mt5()

    # 2. Load TRAINING data
    print("Loading MT5 training data...")
    train_start = pd.to_datetime(cfg.TRAIN_START)
    train_end   = pd.to_datetime(cfg.TRAIN_END)
    df_train = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, train_start, train_end)
    print(f"Loaded {len(df_train)} training bars")

    # 3. Train model
    print("Training model...")
    # model, feature_cols = train_model(df_train)
    model, feature_cols = train_model(df_train, model_params=model_params, horizon=horizon)

    # 4. Load TEST data
    print("Loading MT5 test data...")
    test_start = pd.to_datetime(cfg.TEST_START)
    test_end   = pd.to_datetime(cfg.TEST_END)
    df_test = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, test_start, test_end)
    print(f"Loaded {len(df_test)} test bars")

    # 5. Generate signals on TEST data
    print("Generating signals...")
    df_feat, signals, conf = generate_signals(model, df_test, feature_cols)

    # 6. Backtest
    print("Running backtest...")
    final_balance, equity_df, trades_df = backtest_hedging(
        df_feat, signals, conf,
        sl_mult=sl_mult,
        tp_mult=tp_mult,
        initial_balance=cfg.INITIAL_BALANCE,
        position_size=cfg.POSITION_SIZE,
        conf_threshold=conf_threshold,
        atr_norm_threshold=atr_norm_threshold,
        contr_size=1,
        lev=cfg.LEVARAGE,
        marg_limit=cfg.MARGIN_LIMIT
    )

    # === Sharpe Ratio ===
    # Compute returns from equity curve
    equity_df["returns"] = equity_df["equity"].pct_change()

    # Remove NaN and zero-variance cases
    ret = equity_df["returns"].dropna()

    if ret.std() == 0:
        sharpe = 0
    else:
        # Annualization factor for M5 data
        periods_per_year = 288 * 252  # 288 M5 bars per day × 252 trading days
        sharpe = (ret.mean() / ret.std()) * (periods_per_year ** 0.5)

    # === Trade diagnostics ===
    long_trades = trades_df[trades_df["direction"] == 1]
    short_trades = trades_df[trades_df["direction"] == -1]

    long_wins = long_trades[long_trades["pnl"] > 0]
    short_wins = short_trades[short_trades["pnl"] > 0]

    long_win_rate = len(long_wins) / len(long_trades) if len(long_trades) > 0 else 0
    short_win_rate = len(short_wins) / len(short_trades) if len(short_trades) > 0 else 0
    overall_win_rate = len(trades_df[trades_df["pnl"] > 0]) / len(trades_df) if len(trades_df) > 0 else 0

    # === Holding time diagnostics ===
    trades_df["holding_time"] = trades_df["exit_time"] - trades_df["entry_time"]

    avg_hold_all = trades_df["holding_time"].mean()

    avg_hold_long = (
        trades_df[trades_df["direction"] == 1]["holding_time"].mean()
        if len(long_trades) > 0 else pd.Timedelta(0)
    )

    avg_hold_short = (
        trades_df[trades_df["direction"] == -1]["holding_time"].mean()
        if len(short_trades) > 0 else pd.Timedelta(0)
    )

    # 7. Print summary
    print("\n=== Out-of-Sample Backtest Summary ===")
    print(f"Initial balance: {cfg.INITIAL_BALANCE:.2f}")
    print(f"Final balance:   {final_balance:.2f}")
    print(f"Net PnL:         {final_balance - cfg.INITIAL_BALANCE:.2f} "
          f"({(final_balance / cfg.INITIAL_BALANCE - 1) * 100:.2f}%)")
    print(f"Sharpe ratio:     {sharpe:.2f}")
    print(f"Total trades:    {len(trades_df)}")
    print(f"Long trades:      {len(long_trades)}")
    print(f"Short trades:     {len(short_trades)}")
    print(f"Long win rate:    {long_win_rate:.2%}")
    print(f"Short win rate:   {short_win_rate:.2%}")
    print(f"Overall win rate: {overall_win_rate:.2%}")
    print(f"Average holding time (all):   {avg_hold_all}")
    print(f"Average holding time (long):  {avg_hold_long}")
    print(f"Average holding time (short): {avg_hold_short}")

    # 8. Plot equity
    print("Plotting equity curve...")
    plot_equity(equity_df)

    return model, df_feat, equity_df, trades_df


# def run_full_pipeline():
#     print("=== SignalEngine: Full Pipeline ===")
#
#     # 1. Init MT5
#     print("Initializing MT5...")
#     init_mt5()
#
#     # 2. Load historical data
#     print("Loading MT5 data...")
#     start = pd.to_datetime(cfg.TEST_START)
#     end = pd.to_datetime(cfg.TEST_END)
#     df_raw = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, start, end)
#
#     # 3. Train model
#     print("Training model...")
#     model, feature_cols = train_model(df_raw)
#
#     # 4. Generate signals
#     print("Generating signals...")
#     df_feat, signals, conf = generate_signals(model, df_raw, feature_cols)
#
#     # 5. Backtest
#     print("Running backtest...")
#     final_balance, equity_df, trades_df = backtest_hedging(
#         df_feat, signals, conf,
#         sl_mult=cfg.SL_MULT,
#         tp_mult=cfg.TP_MULT,
#         initial_balance=cfg.INITIAL_BALANCE,
#         position_size=cfg.POSITION_SIZE,
#         conf_threshold=cfg.CONF_THRESHOLD,
#         atr_norm_threshold=cfg.ATR_NORM_THRESHOLD,
#         contr_size=1,
#         lev=20,
#         marg_limit=0.5
#     )
#
#     # 6. Print summary
#     print("\n=== Backtest Summary ===")
#     print(f"Initial balance: {cfg.INITIAL_BALANCE:.2f}")
#     print(f"Final balance:   {final_balance:.2f}")
#     print(f"Net PnL:         {final_balance - cfg.INITIAL_BALANCE:.2f} "
#           f"({(final_balance / cfg.INITIAL_BALANCE - 1) * 100:.2f}%)")
#     print(f"Total trades:    {len(trades_df)}")
#
#     # 7. Plot equity
#     print("Plotting equity curve...")
#     plot_equity(equity_df)
#
#     return model, df_feat, equity_df, trades_df
