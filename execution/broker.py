# execution/broker.py

import MetaTrader5 as mt5
from config import settings as cfg


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


def close_all_if_needed():
    # Here you can implement:
    # - daily loss limit
    # - max open positions
    # - margin checks
    # For now, you can leave it as a stub or implement later.
    pass
