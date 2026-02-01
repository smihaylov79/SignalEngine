# live/live_trader.py

import time
import pandas as pd
from datetime import datetime, timedelta

from config import settings as cfg
from features.pipeline import build_features
from live.mt5_client import init_mt5, get_mt5_rates, get_bars
from models.registry import generate_signals  # your existing function
from models.live_loader import load_live_model
from execution.broker import open_position, close_all_if_needed  # you’ll wire these
from utils.logging import log_event, log_margin_state, log_csv  # simple logger
from execution.margin import compute_required_margin, margin_allowed


def get_lookback_start(now: datetime, bars: int = 300):
    # 300 M5 bars ≈ 25 hours
    delta = timedelta(minutes=5 * bars)
    return now - delta


def live_trading_loop():
    init_mt5()
    model, feature_cols = load_live_model()

    last_bar_time = None

    while True:
        # now = datetime.utcnow()
        # lookback_start = get_lookback_start(now)
        #
        # df_raw = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, lookback_start, now)

        df_raw = get_bars(cfg.SYMBOL, cfg.TIMEFRAME, n=300)

        if df_raw is None or df_raw.empty:
            time.sleep(5)
            continue

        current_bar_time = df_raw.index[-1]

        # Only act once per new M5 bar
        if current_bar_time == last_bar_time:
            time.sleep(5)
            continue

        last_bar_time = current_bar_time

        # Build features and generate signals on full window
        df_feat, preds, conf = generate_signals(model, df_raw, feature_cols)

        # Use last bar only
        last_idx = df_feat.index[-1]
        last_conf = conf[-1]
        last_pred = preds[-1]  # already decoded to -1, 0, 1
        last_atr_norm = df_feat["atr_norm"].iloc[-1]

        # Safety: close all if margin / risk breached
        close_all_if_needed()

        # Filters (use baseline params)
        if last_conf < cfg.CONF_THRESHOLD:
            # log_event(f"{last_idx} | No trade: low confidence {last_conf:.3f}")
            log_csv(
                "NO_TRADE_LOW_CONF",
                bar_time=str(last_idx),
                confidence=last_conf,
            )

            continue

        if last_atr_norm < cfg.ATR_NORM_THRESHOLD:
            # log_event(f"{last_idx} | No trade: low ATR_norm {last_atr_norm:.6f}")
            log_csv(
                "NO_TRADE_LOW_ATR",
                bar_time=str(last_idx),
                atr_norm=last_atr_norm,
            )

            continue

        # Direction: -1 short, 1 long, 0 no trade
        direction = last_pred
        if direction == 0:
            # log_event(f"{last_idx} | No trade: neutral signal")
            log_csv(
                "NO_TRADE_NEUTRAL",
                bar_time=str(last_idx),
            )

            continue

        # Position sizing (simple fixed size for now)
        volume = cfg.POSITION_SIZE

        # Margin check
        required_margin = compute_required_margin(cfg.SYMBOL, direction, volume)

        if required_margin is None:
            # log_event(f"{last_idx} | Cannot compute margin — skipping trade")
            log_csv(
                "CAN_NOT_COMPUTE_MARGIN",
                bar_time=str(last_idx),
            )
            continue

        log_margin_state(f"{last_idx}", direction, required_margin)

        if not margin_allowed(required_margin, direction, cfg.MARGIN_LIMIT):
            # log_event(
            #     f"{last_idx} | Trade blocked: required margin {required_margin:.2f} "
            #     f"exceeds allowed {cfg.MARGIN_LIMIT * 100:.0f}% of equity"
            # )
            log_csv(
                "TRADE_BLOCKED_MARGIN",
                bar_time=str(last_idx),
                direction="LONG" if direction == 1 else "SHORT",
                required_margin=required_margin,
            )

            continue

        # SL/TP in price terms (you already use ATR in backtest)
        atr = df_feat["atr"].iloc[-1]
        sl_dist = cfg.SL_MULT * atr
        tp_dist = cfg.TP_MULT * atr

        open_position(
            symbol=cfg.SYMBOL,
            direction=direction,
            volume=volume,
            sl_distance=sl_dist,
            tp_distance=tp_dist,
            conf=last_conf,
        )

        # log_event(
        #     f"{last_idx} | OPEN {('LONG' if direction == 1 else 'SHORT')} "
        #     f"conf={last_conf:.3f}, atr_norm={last_atr_norm:.6f}, "
        #     f"SL={sl_dist:.5f}, TP={tp_dist:.5f}"
        # )
        log_csv(
            "OPEN_TRADE",
            bar_time=str(last_idx),
            direction="LONG" if direction == 1 else "SHORT",
            confidence=last_conf,
            atr_norm=last_atr_norm,
            sl=sl_dist,
            tp=tp_dist,
            volume=volume,
        )

        # Small sleep to avoid hammering MT5
        time.sleep(5)
