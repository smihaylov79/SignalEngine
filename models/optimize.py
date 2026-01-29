import optuna
import numpy as np
import pandas as pd
import json
import os

from config import settings as cfg
from features.pipeline import build_features
from labeling.targets import add_directional_target
from live.mt5_client import get_mt5_rates, init_mt5
from models.train import XGBClassifier  # or import from your train module
from models.registry import generate_signals
from backtesting.engine import backtest_hedging


def _train_model_with_params(df_train: pd.DataFrame, params: dict):
    df_feat = build_features(df_train)
    df_lab = add_directional_target(df_feat, horizon=params["horizon"])

    X = df_lab.drop(columns=["target", "target_raw", "future_ret"])
    y = df_lab["target"]

    # no shuffle: keep time order
    split_idx = int(len(X) * (1 - cfg.VALIDATION_RATIO))
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    model = XGBClassifier(
        max_depth=params["max_depth"],
        learning_rate=params["learning_rate"],
        n_estimators=params["n_estimators"],
        subsample=params["subsample"],
        colsample_bytree=params["colsample_bytree"],
        min_child_weight=params["min_child_weight"],
        gamma=params["gamma"],
        objective="multi:softprob",
        num_class=3,
    )
    model.fit(X_train, y_train)

    return model, X.columns, df_feat.iloc[split_idx:]  # features aligned with val part


def _compute_sharpe(equity_df: pd.DataFrame) -> float:
    equity_df = equity_df.copy()
    equity_df["returns"] = equity_df["equity"].pct_change()
    ret = equity_df["returns"].dropna()

    if ret.std() == 0 or len(ret) < 10:
        return 0.0

    periods_per_year = 288 * 252  # M5 bars
    sharpe = (ret.mean() / ret.std()) * np.sqrt(periods_per_year)
    return float(sharpe)


def objective(trial: optuna.Trial) -> float:
    # 1) Load TRAIN window only

    train_start = pd.to_datetime(cfg.TRAIN_START)
    train_end = pd.to_datetime(cfg.TRAIN_END)
    df_raw = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, train_start, train_end)

    # 2) Suggest parameters (no indicators here)
    params = {
        # model
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 10.0),
        "gamma": trial.suggest_float("gamma", 0.0, 5.0),

        # target horizon
        "horizon": trial.suggest_int("horizon", 6, 24),

        # execution / thresholds
        "sl_mult": trial.suggest_float("sl_mult", 1.0, 2.5),
        "tp_mult": trial.suggest_float("tp_mult", 1.5, 3.5),
        "conf_threshold": trial.suggest_float("conf_threshold", 0.50, 0.80),
        "atr_norm_threshold": trial.suggest_float("atr_norm_threshold", 0.0003, 0.0020),
    }

    # 3) Train model on early part of TRAIN, validate on late part of TRAIN
    model, feature_cols, df_val_feat = _train_model_with_params(df_raw, params)

    # 4) Generate signals on validation slice
    df_feat_val, signals_val, conf_val = generate_signals(
        model, df_val_feat, feature_cols
    )

    # 5) Backtest on validation slice only (still inside TRAIN window)
    final_balance, equity_df, trades_df = backtest_hedging(
        df_feat_val,
        signals_val,
        conf_val,
        sl_mult=params["sl_mult"],
        tp_mult=params["tp_mult"],
        initial_balance=cfg.INITIAL_BALANCE,
        position_size=cfg.POSITION_SIZE,
        conf_threshold=params["conf_threshold"],
        atr_norm_threshold=params["atr_norm_threshold"],
        contr_size=1,
        lev=20,
        marg_limit=0.5,
    )
    # If no equity points or no trades → return a very bad score
    if equity_df is None or len(equity_df) == 0 or len(trades_df) == 0:
        return -1e6  # or any very low number

    # 6) Use Sharpe on validation as objective
    sharpe = _compute_sharpe(equity_df)
    pnl = final_balance - cfg.INITIAL_BALANCE

    # Normalize PnL to avoid huge scale differences
    pnl_norm = pnl / cfg.INITIAL_BALANCE

    # Combined objective
    objective_value = sharpe * pnl_norm

    # Penalize too few trades
    if len(trades_df) < 50:
        objective_value *= 0.5

    return objective_value


def run_optimization(n_trials: int = 50):
    init_mt5()
    print(f'Running optimization for {n_trials} trials')
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    print("\n=== Optimization finished ===")
    print(f"Best Sharpe: {study.best_value:.4f}")
    print("Best params:")
    for k, v in study.best_params.items():
        print(f"  {k}: {v}")

    # Save best parameters to JSON
    save_path = os.path.join("config", "best_params.json")
    with open(save_path, "w") as f:
        json.dump(study.best_params, f, indent=4)

    print(f"\nSaved best parameters to {save_path}")

    return study

