import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split

from config import settings as cfg
from features.pipeline import build_features
from labeling.targets import add_directional_target

import MetaTrader5 as mt5

from live.mt5_client import get_mt5_rates
import joblib
import os


def load_mt5_data():
    # assumes MT5 already initialized
    from datetime import datetime
    start = pd.to_datetime(cfg.TEST_START)
    end = pd.to_datetime(cfg.TEST_END)
    df = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, start, end)
    return df


def train_model(df_raw, model_params=None, horizon=None, baseline=False):
    if baseline:
        model_params = cfg.BASELINE_PARAMS
        horizon = cfg.BASELINE_HORIZON
    # Slice training window
    df_train = df_raw.loc[cfg.TRAIN_START : cfg.TRAIN_END].copy()

    # Build features + targets
    df_feat = build_features(df_train)
    df_lab = add_directional_target(df_feat, horizon=horizon)

    # Prepare ML data
    X = df_lab.drop(columns=["target", "target_raw", "future_ret"])
    y = df_lab["target"]

    # Validation split inside training window
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=cfg.VALIDATION_RATIO, shuffle=False
    )

    params = model_params or {
        "max_depth": 6,
        "learning_rate": 0.05,
        "n_estimators": 400,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "multi:softprob",
        "num_class": 3,
    }

    model = XGBClassifier(**params)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)
    print(f"Training with horizon = {horizon}")

    score = balanced_accuracy_score(y_val, preds)
    print(f"Validation balanced accuracy: {score:.4f}")
    # Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/saved/baseline_model.pkl")
    # Save feature columns
    joblib.dump(list(X.columns), "models/saved/feature_cols.pkl")
    print("Baseline model and feature columns saved.")

    return model, X.columns

