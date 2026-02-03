import time
from datetime import datetime, timedelta
import pytz

def sleep_until_next_bar(timeframe_minutes=5, tz="Europe/Sofia"):
    now = datetime.now(pytz.timezone(tz))
    minute = (now.minute // timeframe_minutes) * timeframe_minutes
    next_bar = now.replace(minute=minute, second=0, microsecond=0) + timedelta(minutes=timeframe_minutes)

    # Add a small buffer to ensure the bar is fully closed
    next_bar += timedelta(seconds=1)

    sleep_seconds = (next_bar - now).total_seconds()
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
