import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import io
import base64


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def plot_profit_by_conf(df):
    grouped = df.groupby("conf_bucket")["net_profit"].sum()

    fig, ax = plt.subplots(figsize=(10,5))
    grouped.plot(kind="bar", color="steelblue", ax=ax)
    ax.set_title("Net Profit by Confidence Bucket")
    ax.set_xlabel("Confidence Bucket")
    ax.set_ylabel("Net Profit")
    ax.grid(True, alpha=0.3)

    return fig_to_base64(fig)


def plot_profit_by_conf_and_direction(df):
    grouped = df.groupby(["conf_bucket", "direction"])["net_profit"].sum().unstack()

    fig, ax = plt.subplots(figsize=(12,6))
    grouped.plot(kind="bar", ax=ax)
    ax.set_title("Net Profit by Confidence Bucket (Long vs Short)")
    ax.set_xlabel("Confidence Bucket")
    ax.set_ylabel("Net Profit")
    ax.grid(True, alpha=0.3)

    return fig_to_base64(fig)


def plot_confidence_distribution(df):
    winners = df[df["net_profit"] > 0]["confidence"]
    losers = df[df["net_profit"] <= 0]["confidence"]

    fig, ax = plt.subplots(figsize=(10,5))
    ax.hist(winners, bins=20, alpha=0.6, label="Winners", color="green")
    ax.hist(losers, bins=20, alpha=0.6, label="Losers", color="red")
    ax.set_title("Confidence Distribution: Winners vs Losers")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig_to_base64(fig)


def plot_duration_vs_conf(df):
    fig, ax = plt.subplots(figsize=(10,5))
    ax.scatter(df["confidence"], df["duration_sec"], alpha=0.4)
    ax.set_title("Holding Time vs Confidence")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Duration (sec)")
    ax.grid(True, alpha=0.3)

    return fig_to_base64(fig)


#
# def plot_profit_by_conf(df):
#     grouped = df.groupby("conf_bucket")["net_profit"].sum()
#
#     plt.figure(figsize=(10,5))
#     grouped.plot(kind="bar", color="steelblue")
#     plt.title("Net Profit by Confidence Bucket")
#     plt.xlabel("Confidence Bucket")
#     plt.ylabel("Net Profit")
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#
#
# def plot_profit_by_conf_and_direction(df):
#     grouped = df.groupby(["conf_bucket", "direction"])["net_profit"].sum().unstack()
#
#     grouped.plot(kind="bar", figsize=(12,6))
#     plt.title("Net Profit by Confidence Bucket (Long vs Short)")
#     plt.xlabel("Confidence Bucket")
#     plt.ylabel("Net Profit")
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#
#
# def plot_confidence_distribution(df):
#     winners = df[df["net_profit"] > 0]["confidence"]
#     losers = df[df["net_profit"] <= 0]["confidence"]
#
#     plt.figure(figsize=(10,5))
#     plt.hist(winners, bins=20, alpha=0.6, label="Winners", color="green")
#     plt.hist(losers, bins=20, alpha=0.6, label="Losers", color="red")
#     plt.title("Confidence Distribution: Winners vs Losers")
#     plt.xlabel("Confidence")
#     plt.ylabel("Count")
#     plt.legend()
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#
#
# def plot_duration_vs_conf(df):
#     plt.figure(figsize=(10,5))
#     plt.scatter(df["confidence"], df["duration_sec"], alpha=0.4)
#     plt.title("Holding Time vs Confidence")
#     plt.xlabel("Confidence")
#     plt.ylabel("Duration (sec)")
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#
#
#
