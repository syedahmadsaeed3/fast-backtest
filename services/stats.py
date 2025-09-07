from datetime import timedelta

import quantstats as qs

from services.helper_classes import PriceCache
from services.utils import get_security_group_names, get_portfolio_valuation_list


def get_live_strat_lookback_period(data):
    max_period = 0
    for i in data.buy:
        for value in i.values():
            for key in value.keys():
                if "period" in key and value[key] > max_period:
                    max_period = value[key]
    for i in data.sell:
        for value in i.values():
            for key in value.keys():
                if "period" in key and value[key] > max_period:
                    max_period = value[key]
    if data.customized_buy_signal or data.customized_sell_signal:
        for cust in data.customized_buy_signal:
            for i in cust.dict()['strategy']:
                for value in i.values():
                    for key in value.keys():
                        if "period" in key and value[key] > max_period:
                            max_period = value[key]
        for cust in data.customized_sell_signal:
            for i in cust.dict()['strategy']:
                for value in i.values():
                    for key in value.keys():
                        if "period" in key and value[key] > max_period:
                            max_period = value[key]
    return max_period


def get_total_return_percentage(init_cash, total_return):
    return (total_return - init_cash)/init_cash * 100


def win_rate(trades):
    win = 0
    lose = 0
    last_valuation = trades[0]['total_valuation']
    for trade in trades:
        if trade and "active" not in trade:
            if round(trade['total_valuation'],3) > round(last_valuation,3):
                win += 1
            elif round(trade['total_valuation'],3) < round(last_valuation,3):
                lose += 1
            last_valuation = trade['total_valuation']
    return win/(win+lose) * 100


def get_max_drawdown(trades):
    # formula: (peak - trough)/peak * 100
    max_drawdown = 0
    first_trade = trades[0]
    for trade in trades[1:]:
        min_total_valuation = 0
        max_total_valuation = 0
        if first_trade and "active" not in first_trade and "cash" not in first_trade:
            securities = get_security_group_names(first_trade)
            price_cache = PriceCache()
            for sec in securities:
                # get the prices of security in trade period
                prices_in_period = price_cache.get_prices_in_date_range(sec, first_trade['entry_date'], trade['entry_date'])
                min_price = min(prices_in_period, key=lambda x: x.close)
                max_price = max(prices_in_period, key=lambda x: x.close)
                max_total_valuation += max_price.close * first_trade[sec]['shares']
                min_total_valuation += min_price.close * first_trade[sec]['shares']
            drawdown = abs(max_total_valuation - min_total_valuation)/max_total_valuation * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        first_trade = trade
    return max_drawdown


def get_number_of_trades(trades):
    return len(list(filter(None, trades)))


def get_average_trade_length(trades):
    """
    TODO: add exit date and entry date to trades
    """
    trades = [x for x in trades if x]
    trade_lengths = []
    t = trades[0]
    for ind, trade in enumerate(trades):
        if ind > 0:
            trade_lengths.append(trade['entry_date'] - t['entry_date'])
        t = trade
    return sum(trade_lengths, timedelta(0)) / len(trade_lengths) if len(trade_lengths) > 0 else timedelta(0)


def get_stats(trades):
    # get not None last trade
    not_null_trades = [x for x in trades if x]
    last_trade = not_null_trades[-1]
    first_trade = not_null_trades[0]
    total_valuation = 0
    if "cash" not in last_trade:
        for key in last_trade:
            if key != 'cash_before_trade' and key != 'cash_remaining' and \
                    key != 'total_valuation' and key != 'entry_date' and key != 'active':
                total_valuation += last_trade[key]['price']*last_trade[key]['shares']
        total_valuation = total_valuation + last_trade['cash_remaining']
    else:
        total_valuation = last_trade['cash']
    stats = {
        "Start Value": f'{1000000:,}',
        "End Value": f"${round(total_valuation, 2):,}",
        "Start": str(first_trade['entry_date']),
        "End": str(last_trade['entry_date']),
        "Total Return [%]": f"{round(get_total_return_percentage(1000000, total_valuation), 2)}",
        "Win Rate [%]": f"{round(win_rate(trades), 2)}",
        "Max Drawdown [%]": str(round(qs.stats.max_drawdown(get_portfolio_valuation_list),2)),
        "Total Trades": str(get_number_of_trades(trades)),
        "Avg Trade Duration": str(get_average_trade_length(trades))
    }
    return stats