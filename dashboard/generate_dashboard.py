# dashboard/generate_dashboard.py

from datetime import datetime, time
import pandas as pd


from dashboard.database import TradeDatabase
from dashboard.metrics import add_confidence_bucket, profit_by_confidence, profit_by_conf_and_direction
# from dashboard.plotting import plot_profit_by_conf, plot_profit_by_conf_and_direction, plot_confidence_distribution, \
#     plot_duration_vs_conf
from dashboard.data_extraction import TradeDataExtractor
from config import settings as cfg
from dashboard.html_report import generate_html_report
from dashboard.paths import REPORT_PATH


def basic_summary(df: pd.DataFrame, return_string: bool = False):
    lines = []
    lines.append("=== BASIC STATS ===")
    lines.append(f"Trades: {len(df)}")
    lines.append(f"Net profit: {df['net_profit'].sum():.2f}")
    lines.append(f"Avg trade: {df['net_profit'].mean():.2f}")
    lines.append(f"Win rate: {(df['net_profit'] > 0).mean() * 100:.1f}%")

    lines.append("\n=== BY DIRECTION ===")
    lines.append(str(df.groupby("direction")["net_profit"].agg(["count", "sum", "mean"])))

    lines.append("\n=== BY HOUR OF DAY (ENTRY) ===")
    df["entry_hour"] = df["entry_time"].dt.hour
    lines.append(str(df.groupby("entry_hour")["net_profit"].agg(["count", "sum", "mean"])))

    summary_text = "\n".join(lines)

    if return_string:
        return summary_text
    else:
        print(summary_text)


def generate_db_file():
    start_str = cfg.HYSTORY_START
    end_str = cfg.HYSTORY_END
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    TradeDataExtractor.from_mt5_history(start=start_dt, end=end_dt, store_sqlite=True)


def generate_dashboard():
    df = TradeDatabase.load_trades()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])

    df = add_confidence_bucket(df, bucket_size=0.05)
    summary = basic_summary(df, return_string=True)
    profit_conf = profit_by_confidence(df)
    profit_conf_dir = profit_by_conf_and_direction(df)
    report_path = generate_html_report(df, summary, profit_conf, profit_conf_dir, output_path=REPORT_PATH)
    return report_path

#
#
# if __name__ == "__main__":
#     # Example: last 3 days
#     start_str = cfg.HYSTORY_START
#     end_str = cfg.HYSTORY_END
#     start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
#     end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
#     start_dt = datetime.combine(start_date, time.min)
#     end_dt = datetime.combine(end_date, time.max)
#
#     # df = TradeDataExtractor.from_mt5_history(start=start_dt, end=end_dt, store_sqlite=True)
#     df = TradeDatabase.load_trades()
#     df["entry_time"] = pd.to_datetime(df["entry_time"])
#     df["exit_time"] = pd.to_datetime(df["exit_time"])
#
#     df = add_confidence_bucket(df, bucket_size=0.05)
#     summary = basic_summary(df, return_string=True)
#     profit_conf = profit_by_confidence(df)
#     profit_conf_dir = profit_by_conf_and_direction(df)
#     generate_html_report(df, summary, profit_conf, profit_conf_dir)
    #
    # basic_summary(df)
    #
    # print(profit_by_confidence(df))
    # print(profit_by_conf_and_direction(df))
    #
    # plot_profit_by_conf(df)
    # plot_profit_by_conf_and_direction(df)
    # plot_confidence_distribution(df)
    # plot_duration_vs_conf(df)


