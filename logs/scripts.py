import csv

input_file = "live_trading.csv"

margin_file = "margin_log.csv"
trade_file = "trades_log.csv"
lowconf_file = "low_conf_log.csv"

# Define headers
margin_header = [
    "timestamp","event","direction","required_margin","long_used","short_used",
    "avail_long","avail_short","equity","free_margin","margin_level"
]

trade_header = [
    "timestamp","event","trade_time","direction","confidence","atr_norm",
    "sl","tp","volume"
]

lowconf_header = [
    "timestamp","event","trade_time","confidence"
]

# Open output files
with open(margin_file, "w", newline="") as m, \
     open(trade_file, "w", newline="") as t, \
     open(lowconf_file, "w", newline="") as l:

    margin_writer = csv.writer(m)
    trade_writer = csv.writer(t)
    lowconf_writer = csv.writer(l)

    margin_writer.writerow(margin_header)
    trade_writer.writerow(trade_header)
    lowconf_writer.writerow(lowconf_header)

    # Read input
    with open(input_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip original header

        for row in reader:
            event = row[1]

            if event == "MARGIN_CHECK":
                margin_writer.writerow(row)

            elif event == "OPEN_TRADE":
                trade_writer.writerow(row)

            elif event in ("NO_TRADE_LOW_CONF", "TRADE_BLOCKED_MARGIN"):
                lowconf_writer.writerow(row)
