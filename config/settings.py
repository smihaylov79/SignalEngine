# Global settings for SignalEngine

SYMBOL = "[SP500]"
TIMEFRAME = "M5"

HORIZON = 12  # bars ahead for target
TRAIN_START = "2025-06-01"
TRAIN_END = "2025-12-31"
TEST_START = "2026-01-01"
TEST_END = "2026-01-28"
VALIDATION_RATIO = 0.2
LOCAL_TZ = "Europe/Sofia"

SL_MULT = 1.5
TP_MULT = 2.2

INITIAL_BALANCE = 2000
POSITION_SIZE = 1.0

CONF_THRESHOLD = 0.55
ATR_NORM_THRESHOLD = 0.0005

MODEL_TYPE = "xgb"  # future: "lgbm", "rf"
BEST_PARAMS_PATH = "config/best_params.py"  # or json later
OPTIMIZATION_TRIALS = 100
MARGIN_LIMIT = 0.7
LEVARAGE = 20

BASELINE_PARAMS = {
    "max_depth": 6,
    "learning_rate": 0.05,
    "n_estimators": 400,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "objective": "multi:softprob",
    "num_class": 3,
}

BASELINE_HORIZON = 12

MAX_SLIPPAGE = 10
MAGIC_NUMBER = 12345

