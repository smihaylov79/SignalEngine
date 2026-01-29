import numpy as np
import pandas as pd
from features.pipeline import build_features
from labeling.targets import DECODE_MAP
from config import settings as cfg


def generate_signals(model, df_raw, feature_cols):
    df_feat = build_features(df_raw)
    X = df_feat[feature_cols]

    proba = model.predict_proba(X)
    preds_encoded = model.predict(X)
    preds = [DECODE_MAP[p] for p in preds_encoded]  # back to -1,0,1
    conf = proba.max(axis=1)

    return df_feat, preds, conf

