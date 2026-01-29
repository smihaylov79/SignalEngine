import joblib


def load_live_model():
    model = joblib.load("models/saved/baseline_model.pkl")
    feature_cols = joblib.load("models/saved/feature_cols.pkl")
    return model, feature_cols
