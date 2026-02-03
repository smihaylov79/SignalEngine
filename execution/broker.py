# execution/broker.py

import MetaTrader5 as mt5
from config import settings as cfg
from utils.logging import log_event, log_csv, closed_trades_log_csv


def open_position(symbol, direction, volume, sl_distance, tp_distance, conf):
    # direction: 1 = long, -1 = short
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return

    price = tick.ask if direction == 1 else tick.bid
    sl = price - sl_distance if direction == 1 else price + sl_distance
    tp = price + tp_distance if direction == 1 else price - tp_distance

    order_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": cfg.MAX_SLIPPAGE,
        "magic": cfg.MAGIC_NUMBER,
        "comment": f"conf:{conf}",
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    mt5.order_send(request)


def check_reverse_exit(position, new_signal, current_price):
    """
    position: MT5 position object
    new_signal: "LONG", "SHORT", or None
    current_price: float
    """

    if new_signal is None:
        return False

    # 1. Check direction conflict
    if position.type == mt5.ORDER_TYPE_BUY and new_signal == "SHORT":
        reverse = True
    elif position.type == mt5.ORDER_TYPE_SELL and new_signal == "LONG":
        reverse = True
    else:
        reverse = False

    if not reverse:
        return False

    # 2. Check profit
    profit = position.profit
    if profit <= 0:
        return False

    # 3. Check TP not hit
    if position.tp > 0 and (
        (position.type == mt5.ORDER_TYPE_BUY and current_price >= position.tp) or
        (position.type == mt5.ORDER_TYPE_SELL and current_price <= position.tp)
    ):
        return False

    return True


def check_open_positions(signal, last_idx):
    positions = mt5.positions_get(symbol=cfg.SYMBOL)
    last_price = mt5.symbol_info_tick(cfg.SYMBOL).last

    for pos in positions:
        if check_reverse_exit(pos, signal, last_price):
            result = close_position(pos, comment="REVERSE_EXIT")
            closed_trades_log_csv(
                "CLOSE_TRADE",
                bar_time=str(last_idx),
                ticket=pos.ticket,
                profit=pos.profit,
                comment="REVERSE_EXIT"
            )


def close_position(position, comment="CLOSE"):
    symbol = position.symbol
    volume = position.volume
    ticket = position.ticket

    # Determine opposite order type
    if position.type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": cfg.MAGIC_NUMBER,
        "comment": comment,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Failed to close position {ticket}: {result.retcode}")
    else:
        print(f"✅ Closed position {ticket} with comment '{comment}'")

    return result


def close_all_if_needed():
    # Here you can implement:
    # - daily loss limit
    # - max open positions
    # - margin checks
    # For now, you can leave it as a stub or implement later.
    pass


