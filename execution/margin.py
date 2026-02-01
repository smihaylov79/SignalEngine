import MetaTrader5 as mt5

from utils.logging import log_event


def compute_required_margin(symbol, direction: int, volume: float):
    """
    direction: 1 = long, -1 = short
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return None

    price = symbol_info.ask if direction == 1 else symbol_info.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL

    margin = mt5.order_calc_margin(order_type, symbol, volume, price)
    return margin


def margin_allowed(required_margin: float, direction: int, margin_limit: float) -> bool:
    account_info = mt5.account_info()
    if account_info is None:
        return False

    equity = account_info.equity
    allowed_margin = equity * margin_limit

    long_used, short_used = get_long_short_margin()

    available_long = allowed_margin - long_used
    available_short = allowed_margin - short_used

    log_event(
        f"MARGIN_ALLOWED_CHECK | dir={'LONG' if direction == 1 else 'SHORT'} | "
        f"req={required_margin:.2f} | allowed={allowed_margin:.2f} | "
        f"long_used={long_used:.2f} | short_used={short_used:.2f}"
    )

    if direction == 1:   # LONG
        return required_margin <= available_long

    if direction == -1:  # SHORT
        return required_margin <= available_short

    return False


def get_position_margin(p):
    order_type = mt5.ORDER_TYPE_BUY if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL
    return mt5.order_calc_margin(order_type, p.symbol, p.volume, p.price_open)


def get_long_short_margin():
    positions = mt5.positions_get()
    long_used = 0.0
    short_used = 0.0

    if positions:
        for p in positions:
            margin = get_position_margin(p)
            if margin is None:
                continue

            if p.type == mt5.ORDER_TYPE_BUY:
                long_used += margin
            elif p.type == mt5.ORDER_TYPE_SELL:
                short_used += margin

    return long_used, short_used


# def margin_allowed(required_margin: float, margin_limit: float) -> bool:
#     account_info = mt5.account_info()
#     if account_info is None:
#         return False
#
#     equity = account_info.equity
#     current_used = account_info.margin
#
#     allowed_margin = equity * margin_limit
#     new_total = current_used + required_margin
#
#     return new_total <= allowed_margin

