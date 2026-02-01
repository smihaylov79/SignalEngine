from pathlib import Path
import os
import webbrowser

import pandas as pd

from dashboard.generate_dashboard import basic_summary, generate_db_file, generate_dashboard
from dashboard.html_report import generate_html_report
from dashboard.metrics import add_confidence_bucket, profit_by_confidence, profit_by_conf_and_direction

from live.live_trader import live_trading_loop
from live.mt5_client import init_mt5, get_mt5_rates
from models.optimize import run_optimization
from models.train import train_model
from backtesting.reports import run_backtest, plot_equity
from pipeline.run_full import run_full_pipeline
from config import settings as cfg



def run_train(baseline):
    init_mt5()
    train_start = pd.to_datetime(cfg.TRAIN_START)
    train_end = pd.to_datetime(cfg.TRAIN_END)
    df_train = get_mt5_rates(cfg.SYMBOL, cfg.TIMEFRAME, train_start, train_end)
    train_model(df_train, baseline=baseline)
    print("Training finished.")


def run_backtest_cli():
    init_mt5()
    model, feature_cols = train_model()  # later: load from disk instead
    equity_df, trades_df = run_backtest(model, feature_cols)
    plot_equity(equity_df)


def run_live():
    live_trading_loop()
    print("Live trading placeholder")


def main():
    print("=== SignalEngine ===")
    print("1. Full pipeline (baseline)")
    print("11. Full pipeline (optimized)")
    print("2. Train baseline")
    print("3. Backtest only")
    print("4. Live trading")
    print("5. Optimize")
    print("6. Generate Dashboard DB")
    print("7. Dashboard Report")

    choice = input("Select option: ")

    if choice == "1":
        run_full_pipeline(profile_name="baseline", use_best_params=False)
    elif choice == "11":
        run_full_pipeline(profile_name="optimized", use_best_params=True)
    elif choice == "2":
        run_train(baseline=True)
    elif choice == "3":
        run_backtest_cli()
    elif choice == "4":
        run_live()
    elif choice == "5":
        print("Running optimization...")
        run_optimization(n_trials=cfg.OPTIMIZATION_TRIALS)
    elif choice == "6":
        generate_db_file()
    elif choice == "7":
        report_path = generate_dashboard()
        webbrowser.open(report_path)


    else:
        print("Invalid choice")



if __name__ == "__main__":
    main()


