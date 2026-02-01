from datetime import datetime, time
from config import settings as cfg


def round_dict(d, n=2):
    return {k: round(v, n) if isinstance(v, float) else v for k, v in d.items()}


def rework_time_to_mt5(start=cfg.HYSTORY_START, end=cfg.HYSTORY_END):
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    return start_dt, end_dt