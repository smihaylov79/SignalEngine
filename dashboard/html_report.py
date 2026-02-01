import io
import base64
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from dashboard.plotting import plot_duration_vs_conf, plot_confidence_distribution, plot_profit_by_conf_and_direction, \
    plot_profit_by_conf


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def plot_equity_curve(df: pd.DataFrame) -> str:
    df_sorted = df.sort_values("exit_time").copy()
    df_sorted["equity"] = df_sorted["net_profit"].cumsum()

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df_sorted["exit_time"], df_sorted["equity"], label="Equity", color="#007bff")
    ax.set_title("Equity Curve")
    ax.set_xlabel("Time")
    ax.set_ylabel("Equity")
    ax.grid(True, alpha=0.3)
    return _fig_to_base64(fig)


def plot_drawdown(df: pd.DataFrame) -> str:
    df_sorted = df.sort_values("exit_time").copy()
    equity = df_sorted["net_profit"].cumsum()
    roll_max = equity.cummax()
    drawdown = equity - roll_max

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df_sorted["exit_time"], drawdown, color="#dc3545")
    ax.set_title("Drawdown")
    ax.set_xlabel("Time")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    return _fig_to_base64(fig)


def plot_profit_by_hour(df: pd.DataFrame) -> str:
    df = df.copy()
    df["entry_hour"] = df["entry_time"].dt.hour
    grouped = df.groupby("entry_hour")["net_profit"].sum()

    fig, ax = plt.subplots(figsize=(6, 3))
    grouped.plot(kind="bar", ax=ax, color="#17a2b8")
    ax.set_title("Profit by Hour of Day")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Net Profit")
    ax.grid(True, axis="y", alpha=0.3)
    return _fig_to_base64(fig)


def plot_profit_by_weekday(df: pd.DataFrame) -> str:
    df = df.copy()
    df["weekday"] = df["entry_time"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = df.groupby("weekday")["net_profit"].sum().reindex(order)

    fig, ax = plt.subplots(figsize=(6, 3))
    grouped.plot(kind="bar", ax=ax, color="#28a745")
    ax.set_title("Profit by Day of Week")
    ax.set_xlabel("Day")
    ax.set_ylabel("Net Profit")
    ax.grid(True, axis="y", alpha=0.3)
    return _fig_to_base64(fig)


def build_summary_cards(df):
    long_df = df[df["direction"] == "BUY"]
    short_df = df[df["direction"] == "SELL"]

    cards = [
        ("Total Trades", len(df)),
        ("Long Trades", len(long_df)),
        ("Short Trades", len(short_df)),
        ("Long Win Rate", f"{(long_df['net_profit'] > 0).mean() * 100:.1f}%"),
        ("Short Win Rate", f"{(short_df['net_profit'] > 0).mean() * 100:.1f}%"),
        ("Net Profit", f"{df['net_profit'].sum():.2f}"),
        ("Avg Trade", f"{df['net_profit'].mean():.2f}"),
    ]

    html = '<div class="row">'
    for title, value in cards:
        html += f"""
        <div class="col-md-3 mb-3">
            <div class="card shadow-sm">
                <div class="card-body">
                    <h6 class="card-title text-muted">{title}</h6>
                    <h4 class="card-text">{value}</h4>
                </div>
            </div>
        </div>
        """
    html += "</div>"
    return html


def generate_recommendations(df, profit_conf, profit_conf_dir):
    recs = []

    # 1. Weak confidence buckets
    bad_buckets = profit_conf[profit_conf["mean"] < 0]
    for bucket in bad_buckets.index:
        recs.append(f"Confidence bucket {bucket} shows negative expectancy — avoid trades in this range.")

    # 2. Weak short performance
    short_df = df[df["direction"] == "SELL"]
    if (short_df["net_profit"] > 0).mean() < 0.5:
        recs.append("Short trades underperform — consider reducing short exposure.")

    # 3. Time-based weakness
    df["hour"] = df["entry_time"].dt.hour
    evening_loss = df[df["hour"] >= 18]["net_profit"].sum()
    if evening_loss < 0:
        recs.append("Avoid trading after 18:00 — evening trades show negative performance.")

    # 4. Low-confidence long trades
    low_conf_long = df[(df["direction"] == "BUY") & (df["confidence"] < 0.75)]
    if low_conf_long["net_profit"].sum() < 0:
        recs.append("Long trades with confidence < 0.75 show negative results — consider filtering them out.")

    if not recs:
        recs.append("No major weaknesses detected — strategy appears stable.")

    return recs


def generate_html_report(df, summary, profit_conf, profit_conf_dir, output_path):
    # Period
    start = df["entry_time"].min()
    end = df["exit_time"].max()
    period_str = f"{start:%Y-%m-%d} → {end:%Y-%m-%d}"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Tables
    trades_table_html = df.to_html(classes="table table-sm table-striped table-bordered", index=False)
    profit_conf_table = profit_conf.to_html(classes="table table-sm table-striped table-bordered")
    profit_conf_dir_table = profit_conf_dir.to_html(classes="table table-sm table-striped table-bordered")

    # Plots (all must return base64)
    equity_curve_b64 = plot_equity_curve(df)
    drawdown_b64 = plot_drawdown(df)
    profit_conf_b64 = plot_profit_by_conf(df)
    profit_conf_dir_b64 = plot_profit_by_conf_and_direction(df)
    conf_dist_b64 = plot_confidence_distribution(df)
    duration_conf_b64 = plot_duration_vs_conf(df)
    profit_hour_b64 = plot_profit_by_hour(df)
    profit_weekday_b64 = plot_profit_by_weekday(df)

    # Summary cards
    summary_cards_html = build_summary_cards(df)

    # Recommendations
    recs = generate_recommendations(df, profit_conf, profit_conf_dir)
    recs_html = "<ul>" + "".join(f"<li>{r}</li>" for r in recs) + "</ul>"

    # Raw summary (collapsible)
    summary_html = summary.replace("\n", "<br>")

    # Final HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Trading Performance Dashboard</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        body {{
            background-color: #f8f9fa;
            padding: 20px;
        }}
        .section {{
            background: #ffffff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        img {{
            max-width: 100%;
            border-radius: 6px;
            margin-top: 10px;
        }}
        pre {{
            background: #f1f3f5;
            padding: 15px;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
<div class="container">

    <!-- HEADER -->
    <div class="section">
        <h1>Trading Performance Dashboard</h1>
        <p><strong>Period:</strong> {period_str}</p>
        <p><strong>Generated at:</strong> {generated_at}</p>
    </div>

    <!-- EQUITY & DRAWDOWN -->
    <div class="section">
        <h2>Equity & Drawdown</h2>
        <div class="row">
            <div class="col-md-6">
                <h5>Equity Curve</h5>
                <img src="data:image/png;base64,{equity_curve_b64}" />
            </div>
            <div class="col-md-6">
                <h5>Drawdown</h5>
                <img src="data:image/png;base64,{drawdown_b64}" />
            </div>
        </div>
    </div>

    <!-- SUMMARY -->
    <div class="section">
        <h2>Summary</h2>
        {summary_cards_html}

        <details class="mt-3">
            <summary>Show raw summary</summary>
            <pre>{summary_html}</pre>
        </details>
    </div>

    <!-- RECOMMENDATIONS -->
    <div class="section">
        <h2>Recommendations</h2>
        {recs_html}
    </div>

    <!-- CONFIDENCE ANALYTICS -->
    <div class="section">
        <h2>Confidence Analytics</h2>

        <h5>Profit by Confidence Bucket</h5>
        {profit_conf_table}
        <img src="data:image/png;base64,{profit_conf_b64}" />

        <h5 class="mt-4">Profit by Confidence & Direction</h5>
        {profit_conf_dir_table}
        <img src="data:image/png;base64,{profit_conf_dir_b64}" />

        <h5 class="mt-4">Confidence Distribution (Winners vs Losers)</h5>
        <img src="data:image/png;base64,{conf_dist_b64}" />
    </div>

    <!-- TIME ANALYTICS -->
    <div class="section">
        <h2>Time-Based Analytics</h2>

        <div class="row">
            <div class="col-md-6">
                <h5>Profit by Hour of Day</h5>
                <img src="data:image/png;base64,{profit_hour_b64}" />
            </div>
            <div class="col-md-6">
                <h5>Profit by Day of Week</h5>
                <img src="data:image/png;base64,{profit_weekday_b64}" />
            </div>
        </div>

        <h5 class="mt-4">Duration vs Confidence</h5>
        <img src="data:image/png;base64,{duration_conf_b64}" />
    </div>

    <!-- TRADES TABLE -->
    <div class="section">
        <h2>All Trades</h2>
        <details>
            <summary>Show trades table</summary>
            <div class="mt-3">
                {trades_table_html}
            </div>
        </details>
    </div>

</div>
</body>
</html>
"""

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path



# import base64
# import io
# import pandas as pd
# import matplotlib.pyplot as plt
# import os
#
#
# def fig_to_base64(fig):
#     buf = io.BytesIO()
#     fig.savefig(buf, format="png", bbox_inches="tight")
#     buf.seek(0)
#     encoded = base64.b64encode(buf.read()).decode("utf-8")
#     plt.close(fig)
#     return encoded
#
#
# def generate_html_report(df, summary, profit_conf, profit_conf_dir, output_path):
#     html = f"""
#     <html>
#     <head>
#         <title>Trading Dashboard Report</title>
#         <style>
#             body {{
#                 font-family: Arial, sans-serif;
#                 margin: 20px;
#                 background: #f7f7f7;
#             }}
#             h1, h2 {{
#                 color: #333;
#             }}
#             .section {{
#                 background: white;
#                 padding: 20px;
#                 margin-bottom: 20px;
#                 border-radius: 8px;
#                 box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#             }}
#             table {{
#                 width: 100%;
#                 border-collapse: collapse;
#                 margin-top: 10px;
#             }}
#             th, td {{
#                 border: 1px solid #ccc;
#                 padding: 8px;
#                 text-align: center;
#             }}
#             th {{
#                 background: #eee;
#             }}
#             img {{
#                 max-width: 100%;
#                 border-radius: 6px;
#                 margin-top: 10px;
#             }}
#         </style>
#     </head>
#     <body>
#
#         <h1>Trading Dashboard Report</h1>
#
#         <div class="section">
#             <h2>Summary Statistics</h2>
#             <pre>{summary}</pre>
#         </div>
#
#         <div class="section">
#             <h2>Profit by Confidence Bucket</h2>
#             {profit_conf.to_html()}
#             <img src="data:image/png;base64,{plot_profit_conf(df)}" />
#         </div>
#
#         <div class="section">
#             <h2>Profit by Confidence & Direction</h2>
#             {profit_conf_dir.to_html()}
#             <img src="data:image/png;base64,{plot_profit_conf_dir(df)}" />
#         </div>
#
#         <div class="section">
#             <h2>Confidence Distribution (Winners vs Losers)</h2>
#             <img src="data:image/png;base64,{plot_conf_dist(df)}" />
#         </div>
#
#         <div class="section">
#             <h2>Duration vs Confidence</h2>
#             <img src="data:image/png;base64,{plot_duration_conf(df)}" />
#         </div>
#
#     </body>
#     </html>
#     """
#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write(html)
#     return output_path
#
#
# # --- Plot functions return base64 images ---
#
# def plot_profit_conf(df):
#     fig, ax = plt.subplots(figsize=(8,4))
#     df.groupby("conf_bucket")["net_profit"].sum().plot(kind="bar", ax=ax)
#     ax.set_title("Net Profit by Confidence Bucket")
#     ax.set_xlabel("Confidence Bucket")
#     ax.set_ylabel("Net Profit")
#     ax.grid(True, alpha=0.3)
#     return fig_to_base64(fig)
#
#
# def plot_profit_conf_dir(df):
#     fig, ax = plt.subplots(figsize=(8,4))
#     df.groupby(["conf_bucket", "direction"])["net_profit"].sum().unstack().plot(kind="bar", ax=ax)
#     ax.set_title("Net Profit by Confidence Bucket & Direction")
#     ax.set_xlabel("Confidence Bucket")
#     ax.set_ylabel("Net Profit")
#     ax.grid(True, alpha=0.3)
#     return fig_to_base64(fig)
#
#
# def plot_conf_dist(df):
#     fig, ax = plt.subplots(figsize=(8,4))
#     winners = df[df["net_profit"] > 0]["confidence"]
#     losers = df[df["net_profit"] <= 0]["confidence"]
#     ax.hist(winners, bins=20, alpha=0.6, label="Winners", color="green")
#     ax.hist(losers, bins=20, alpha=0.6, label="Losers", color="red")
#     ax.set_title("Confidence Distribution: Winners vs Losers")
#     ax.set_xlabel("Confidence")
#     ax.set_ylabel("Count")
#     ax.legend()
#     ax.grid(True, alpha=0.3)
#     return fig_to_base64(fig)
#
#
# def plot_duration_conf(df):
#     fig, ax = plt.subplots(figsize=(8,4))
#     ax.scatter(df["confidence"], df["duration_sec"], alpha=0.4)
#     ax.set_title("Duration vs Confidence")
#     ax.set_xlabel("Confidence")
#     ax.set_ylabel("Duration (sec)")
#     ax.grid(True, alpha=0.3)
#     return fig_to_base64(fig)
