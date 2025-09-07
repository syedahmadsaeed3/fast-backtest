import json
from datetime import datetime

import pandas as pd
from plotly import io as pio

from cruds.backtest_activity_crud import create_backtest
from cruds.strategy_portfolio_crud import update_paper_portfolio
from schemas.backtest_activity_schema import BacktestActivity
from schemas.backtest_schema import Backtest
from schemas.strategy_porfolio_schema import SecurityGroup, MetricsPortfolio
from services.helper_classes import UserThread, PriceCache
from services.utils import send_slack_alert, get_orders, date_range
from services.graph import plot_strategy_line
from services.stats import get_live_strat_lookback_period
from services.vectorbt_opensource_service import VectorbtService


def record_paper_portfolio_orders(db, data, user_id):
    pass


def loop_paper_portfolio(data_service, db, data: Backtest, security_group: SecurityGroup, user_id):
    lookback_period = get_live_strat_lookback_period(data)
    user_data = UserThread()
    price_cache = PriceCache()
    response = data_service.get_n_day_data(lookback_period, data.ticker)
    while user_data.get_user_data_by_key(user_id, data.strategy_name) or True:
        # response = []
        signal_security = security_group.security  # for now assume only one security

        response += data_service.get_n_day_data(lookback_period, data.ticker)

        data.limit = lookback_period  # len(response[0])  # get actual days from data
        close, high, low, v = start_backtest(response, db, data, user_id)
        entry, exit = v.get_entries_and_exits()

        if exit.iloc[-1].bool():
            if data.customized_sell_signal:
                pass
            else:
                security_group.shares = 0
        elif entry.iloc[-1].bool():
            if data.customized_buy_signal:
                pass
            else:
                price = price_cache.get_price_at_date(data.ticker, datetime.now())

                security_group.shares = price  # TODO: get total allocated money and divide by price to get shares

        user_data = UserThread()
        user_data.initialize_user(user_id)
        portfolio = user_data.get_user_data_by_key(user_id, 'portfolio')
        pf_buy = user_data.get_user_data_by_key(user_id, 'buy_portfolio')
        pf_sell = user_data.get_user_data_by_key(user_id, 'sell_portfolio')


def debit_available_portfolio_cash(portfolio, strategy_allocation):
    """
    TODO: We can later use this function to define custom logic for re-balancing assets
    """
    if portfolio['liquid_cash'] >= strategy_allocation:
        return portfolio['liquid_cash'] - strategy_allocation
    return None


def looping_run(data_service, db, data, user_id, resolution="d", is_simulated=True):
    while True:
        response = data_service.get_1min_day_data(data.ticker) if resolution == 'd' else \
            data_service.get_n_day_data(data.limit, data.ticker)
        close, high, low, v = start_backtest(response, db, data, user_id)
        entries, exits = v.get_entries_and_exits()

        # TODO: use a more effective method to store signals for data integrity
        user_data = UserThread()
        user_data.initialize_user(user_id)
        user_data.set_user_data_by_key(user_id, 'entries', entries)
        user_data.set_user_data_by_key(user_id, 'exits', exits)

        if exits.iloc[-1].iloc[-1] or entries.iloc[-1].iloc[-1]:
            v.run_portfolio(close, 1000000)
            stats = v.get_max_stats().to_dict()
            user_data.set_user_data_by_key( user_id, "metrics",MetricsPortfolio.parse_obj({
                "user_id": user_id,
                "ticker": data.ticker,
                "strategy_name": data.strategy_name,
                "start_timestamp": stats['Start'],
                "end_timestamp": stats['End'],
                "period": stats['Period'],
                "start_value": stats['Start Value'],
                "end_value": stats['End Value'],
                "total_return": stats['Total Return [%]'],
                "benchmark_return": stats['Benchmark Return [%]'],
                "max_gross_exposure": stats['Max Gross Exposure [%]'],
                "total_fees_paid": stats['Total Fees Paid'],
                "max_drawdown": stats['Max Drawdown [%]'],
                "max_drawdown_duration": stats['Max Drawdown Duration'],
                "total_trades": stats['Total Trades'],
                "total_closed_trades": stats['Total Closed Trades'],
                "total_open_trades": stats['Total Open Trades'],
                "open_trade_pnl": stats['Open Trade PnL'],
                "win_rate": stats['Win Rate [%]'],
                "best_trade": stats['Best Trade [%]'],
                "worst_trade": stats['Worst Trade [%]'],
                "avg_winning_trade": stats['Avg Winning Trade [%]'],
                "avg_losing_trade": stats['Avg Losing Trade [%]'],
                "avg_winning_trade_duration": stats['Avg Winning Trade Duration'],
                "avg_losing_trade_duration": stats['Avg Losing Trade Duration'],
                "profit_factor": stats['Profit Factor'],
                "expectancy": stats['Expectancy'],
                "sharpe_ratio": stats['Sharpe Ratio'],
                "calmar_ratio": stats['Calmar Ratio'],
                "omega_ratio": stats['Omega Ratio'],
                "sortino_ratio": stats['Sortino Ratio']
            }))
            update_paper_portfolio(db, user_id, data.strategy_name, user_data[user_id]['portfolio'])

        if user_data.get_user_data_by_key(user_id, 'slack_webhook'):
            if exits.iloc[-1].iloc[-1]:
                send_slack_alert(f"sell signal generated for {data.strategy_name}")
            elif entries.iloc[-1].iloc[-1]:
                send_slack_alert(f"buy signal generated {data.strategy_name}")


def run_portfolio(v, close, lookback_size=0) -> dict:
    pf = v.run_portfolio(close, 1000000, lookback_size)

    res = {}
    if len(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data']) > 2:
        order_dates = list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][1]['x']) + \
                      list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][2]['x'])
        order_dates.sort()
        buy_order = list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][1]['y'])
        sell_order = list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][2]['y'])
        res['order_details'] = get_orders(order_dates, buy_order, sell_order)
    elif len(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data']) == 2:
        order_dates = list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][0]['x'])
        order_dates.sort()
        buy_order = list(pf.plot_orders(column=pf.wrapper.columns[0]).to_dict()['data'][0]['y'])
        sell_order = []
        res['order_details'] = get_orders(order_dates, buy_order, sell_order)
    else:
        res['order_details'] = []

    stats = v.get_max_stats()
    res['stats'] = json.loads(stats.to_json())
    res['stats']['Period'] = str((datetime.fromtimestamp(res['stats']['End'] / 1000) - datetime.fromtimestamp(
        res['stats']['Start'] / 1000)).days) + ' days'
    res['stats']['Start'] = str(datetime.fromtimestamp(res['stats']['Start'] / 1000)).split(' ')[0]
    res['stats']['End'] = str(datetime.fromtimestamp(res['stats']['End'] / 1000)).split(' ')[0]
    res['stats']['Avg Winning Trade Duration'] = str(stats['Avg Winning Trade Duration']).split(' ')[0]
    res['stats']['Avg Losing Trade Duration'] = str(stats['Avg Losing Trade Duration']).split(' ')[0]
    res['stats']['Max Drawdown Duration'] = str(stats['Max Drawdown Duration']).split(' ')[0]
    res['stats']['Start Value'] = f"{stats['Start Value']:,.2f}"
    res['stats']['End Value'] = f"{stats['End Value']:,.2f}"
    res['stats'].pop('Open Trade PnL')
    res['graph_data'] = pf.plot_trades(column=pf.wrapper.columns[0])
    # res['graph_data'].show()

    if res['graph_data']['layout']['shapes']:
        has_shapes = True
    else:
        has_shapes = False

    res['graph_data'] = json.loads(res['graph_data'].to_json())
    res['graph_data']['data'][0]['line']['color'] = '#84cc16'

    if has_shapes:
        plot_strategy_line(res['graph_data'])
        highlight_y0 = min(min(res['graph_data']['data'][0]['y']), min(res['graph_data']['data'][-1]['y']))
        highlight_y1 = max(max(res['graph_data']['data'][0]['y']), max(res['graph_data']['data'][-1]['y']))

        for i in res['graph_data']['layout']['shapes']:
            i['fillcolor'] = "#84cc16" if i['fillcolor'] == 'green' else '#f43f5e'
            i['y0'] = highlight_y0
            i['y1'] = highlight_y1
    test = pio.from_json(json.dumps(res['graph_data']))
    # test.show()

    return res


def start_backtest(response, db, data, user_id):
    """
    TODO: break this function into 2 parts: (1) running backtest (2) running portfolio.
    TODO: implement function to check entry/exit signals, and make alerts accordingly
    """

    v = VectorbtService()
    close_list = [float(x.close) for x in response]
    high = [float(x.high) for x in response]
    low = [float(x.low) for x in response]
    backtest = BacktestActivity.parse_obj({
        "buy_exp": data.buy_exp,
        "sell_exp": data.sell_exp,
        "days": data.limit,
        "buy": {"data": data.buy},
        "sell": {"data": data.sell},
        "ticker": data.ticker
    })
    backtest = backtest.dict()
    backtest.update({"user_id": user_id})
    create_backtest(db, backtest)
    v.custom_indicator_backtester(response, close_list, high, low,
                                                       {
                                                           "buy": data.buy,
                                                           "sell": data.sell,
                                                           "buy_exp": data.buy_exp,
                                                           "sell_exp": data.sell_exp
                                                       })
    close = pd.DataFrame([float(x.close) for x in response], index=[x.timestamp for x in response])
    high = pd.DataFrame([float(x.high) for x in response], index=[x for x in response])
    low = pd.DataFrame([float(x.low) for x in response], index=[x.timestamp for x in response])
    print('run complete')
    return close, high, low, v


def daily_leverage(security_group, key, cash, start_date, end_date):
    trade_data = {}
    daily_trade = []
    sub_total = 0
    prices = PriceCache()
    for date in date_range(start_date, end_date):
        sub_total = 0
        # buy portfolio for the day
        for sec in security_group[key]:
            amount = sec['allocation'] / 100 * cash
            sec['shares'] = 0 if not sec['shares'] else sec['shares']
            sec['shares'] += (amount / prices.get_price_at_date(sec['security'], date).open)
            sub_total += sec['shares'] * prices.get_price_at_date(sec['security'], date).open
            trade_data.update({
                sec['security']: {
                    "shares": sec['shares'],
                    "price": prices.get_price_at_date(sec['security'], date).open,
                    "total": sub_total
                }
            })
        trade_data.update({"cash_before_trade": cash})
        cash -= sub_total
        trade_data.update({"cash_remaining": cash})
        trade_data.update({"total_valuation": sub_total + cash})
        trade_data.update({"entry_date": date})
        daily_trade.append(trade_data)

        # sell portfolio for the day
        sub_total = 0
        for sec in security_group[key]:
            if sec['shares']:
                cash += sec['shares'] * prices.get_price_at_date(sec['security'], date).close
                sec['shares'] = 0
            trade_data.update({
                sec['security']: {
                    "shares": sec['shares'],
                    "price": prices.get_price_at_date(sec['security'], date).close,
                    "total": sub_total
                }
            })
        trade_data.update({"cash_before_trade": cash})
        cash -= sub_total
        trade_data.update({"cash_remaining": cash})
        trade_data.update({"total_valuation": sub_total + cash})
        trade_data.update({"entry_date": date})
        daily_trade.append(trade_data)

    return daily_trade


def get_portfolio_signal_from_lookback(dates, customized_buy_signal, customized_sell_signal, entries, exits):
    portfolio = None
    signal = "buy"
    for ind, i in enumerate(zip(entries.values, exits.values, dates)):
        entry = i[0]
        exit = i[1]

        if exit:
            for key, items in enumerate(customized_sell_signal):
                sig = list(items.values())[0].values[ind]
                if sig:
                    portfolio = key
                    signal = "sell"
                    break

        elif entry:
            for key, items in enumerate(customized_buy_signal):
                sig = list(items.values())[0].values[ind]
                if sig:
                    portfolio = key
                    signal = "buy"
                    break
    return portfolio, signal


def get_trades(dates, customized_buy_signal, buy_keys, customized_sell_signal, sell_keys, entries, exits, user_id,
               lookback_size):
    """
    here lookback_size in the indices of dates and signals is the number of days (6 months) in the lookback period. This is a
    constant for now, but later, will be input from the user
    """
    user_data = UserThread()
    buy_security_group = user_data.get_user_data_by_key(user_id, 'buy_security_group')
    sell_security_group = user_data.get_user_data_by_key(user_id, 'sell_security_group')
    cash = user_data.get_user_data_by_key(user_id, 'cash')
    prices = PriceCache()
    trades = []
    sub_total = 0
    trade_data = {}
    close_ind = 0
    last_signal = "buy"
    key, to_buy = get_portfolio_signal_from_lookback(dates[:lookback_size], customized_buy_signal[:lookback_size],
                                                     customized_sell_signal[:lookback_size], entries[:lookback_size], exits[:lookback_size])
    if key is not None:
        if to_buy == "sell":
            sec_group = sell_security_group[key]
        else:
            sec_group = buy_security_group[key]
        for sec in sec_group:
            if sec['security'].lower() != "cash":
                amount = sec['allocation'] / 100 * cash
                sec['shares'] = 0 if not sec['shares'] else sec['shares']
                sec['shares'] += amount // prices.get_price_at_date(sec['security'], dates[lookback_size]).close
                sub_total += sec['shares'] * prices.get_price_at_date(sec['security'], dates[lookback_size]).close
                trade_data.update({
                    sec['security']: {
                        "shares": sec['shares'],
                        "price": prices.get_price_at_date(sec['security'], dates[lookback_size]).close,
                        "total": sub_total,
                        "name": sec['security'],
                        "allocation": sec['allocation'],
                    }
                })
                close_ind += 1
        if any(trade_data):
            trade_data.update({"cash_before_trade": cash})
            cash -= sub_total
            trade_data.update({"cash_remaining": cash})
            trade_data.update({"total_valuation": sub_total + cash})
            trade_data.update({"entry_date": dates[lookback_size]})
            print(
                f"------------------------- {dates[lookback_size]} -------------------------")
            print(f"trades :")
            print(trade_data)
            print()
            trades.append(trade_data)

    for ind, i in enumerate(zip(entries.values[lookback_size:], exits.values[lookback_size:], dates[lookback_size:])):
        entry = i[0]
        exit = i[1]
        skip_sell = True

        if exit:
            sig = False
            for key, items in enumerate(customized_sell_signal):
                sig = list(items.values())[0][lookback_size:].values[ind]
                if sig:
                    trade_data = {}
                    # TODO: logic to buy into relevant sell security group
                    # sell all previous buy security group
                    prev_cash = cash
                    for groups in buy_keys:
                        for sec in buy_security_group[groups]:
                            if sec['shares']:
                                cash += sec['shares'] * prices.get_price_at_date(sec['security'], i[-1]).close
                                sec['shares'] = 0

                    close_ind = 0
                    sub_total = 0
                    # buy into sell security group

                    if sell_security_group[key][0]["security"].lower() != "cash":
                        req_cash = cash
                        for sec in sell_security_group[key]:
                            amount = sec['allocation'] / 100 * cash
                            shares = amount / prices.get_price_at_date(sec['security'], i[-1]).close
                            shares = 1 if shares == 0 else shares
                            req_cash -= shares * prices.get_price_at_date(sec['security'], i[-1]).close
                            close_ind += 1

                        close_ind = 0
                        if req_cash >= 0:
                            last_signal = "sell"
                            for sec in sell_security_group[key]:
                                amount = sec['allocation']/100 * cash
                                sec['shares'] = 0 if not sec['shares'] else sec['shares']
                                sec['shares'] += (amount / prices.get_price_at_date(sec['security'], i[-1]).close)
                                sub_total += sec['shares'] * prices.get_price_at_date(sec['security'], i[-1]).close
                                trade_data.update({
                                    sec['security']: {
                                        "shares": sec['shares'],
                                        "price": prices.get_price_at_date(sec['security'], i[-1]).close,
                                        "total": sub_total,
                                        "allocation": sec['allocation'],
                                        "name": sec['security']
                                    }
                                })
                                close_ind += 1
                            trade_data.update({"cash_before_trade": cash})
                            cash = 0
                            trade_data.update({"cash_remaining": cash})
                            trade_data.update({"total_valuation": sub_total + cash})
                            trade_data.update({"entry_date": i[-1]})
                            print(
                                f"------------------------- {i[-1]} -------------------------")
                            print(f"trades :")
                            print(trade_data)
                            print()
                            trades.append(trade_data)
                            skip_sell = False
                            break
                        else:
                            skip_sell = True
                    else:
                        last_signal = "sell"
                        if prev_cash != cash:
                            trades.append({
                                "cash": cash,
                                "entry_date": i[-1],
                                "total_valuation": cash,
                            })
                            skip_sell = False
                        else:
                            skip_sell = True

        if entry and skip_sell:
            skip_sell = True
            sig = False
            for key, items in enumerate(customized_buy_signal):
                sig = list(items.values())[0][lookback_size:].values[ind]
                if sig:
                    trade_data = {}
                    sub_total = 0
                    close_ind = 0
                    # sell all previous sell security group
                    for groups in sell_keys:
                        if sell_security_group[groups][0]["security"] != "cash":
                            for sec in sell_security_group[groups]:
                                if sec['shares']:
                                    cash += sec['shares'] * prices.get_price_at_date(sec['security'], i[-1]).close
                                    sec['shares'] = 0
                                else:
                                    close_ind += 1
                                    break
                                close_ind += 1

                    close_ind = 0
                    req_cash = cash
                    for sec in buy_security_group[key]:
                        amount = sec['allocation']/100 * cash
                        shares = amount / prices.get_price_at_date(sec['security'], i[-1]).close
                        shares = 1 if shares == 0 else shares
                        req_cash -= shares * prices.get_price_at_date(sec['security'], i[-1]).close
                        close_ind += 1

                    close_ind = 0
                    if req_cash >= 0:
                        last_signal = "buy"
                        # buy into buy security group
                        for sec in buy_security_group[key]:
                            amount = sec['allocation']/100 * cash

                            sec['shares'] = 0 if not sec['shares'] else sec['shares']
                            sec['shares'] += amount / prices.get_price_at_date(sec['security'], i[-1]).close
                            sub_total += sec['shares'] * prices.get_price_at_date(sec['security'], i[-1]).close
                            trade_data.update({
                                sec['security']: {
                                    "shares": sec['shares'],
                                    "price": prices.get_price_at_date(sec['security'], i[-1]).close,
                                    "total": sub_total,
                                    "allocation": sec['allocation'],
                                    "name": sec['security']
                                }
                            })
                            close_ind += 1
                        trade_data.update({"cash_before_trade": cash})
                        cash = 0
                        trade_data.update({"cash_remaining": cash})
                        trade_data.update({"total_valuation": sub_total + cash})
                        trade_data.update({"entry_date": i[-1]})
                        print(f"--------------------------{i[-1]}--------------------------")
                        print(f"trades :")
                        print(trade_data)
                        print()
                        trades.append(trade_data)
                        trade_day = False
                        break
    # add to trades if last trade has not been closed
    if "cash" not in trades[-1]:
        if last_signal == "buy":
            keys = buy_keys
        else:
            keys = sell_keys

        total_valuation = 0
        last_trade = trades[-1].copy()
        trades.append(last_trade)
        for groups in keys:
            for sec in buy_security_group[groups]:
                if last_trade[sec['name']]['shares']:
                    total = last_trade[sec['name']]['shares'] * prices.get_last_price(sec['security']).close
                    total_valuation += total
                    # update security price and total
                    trades[-1][sec['security']].update({"total": total})
                    trades[-1][sec['security']].update({"price": prices.get_last_price(sec['security']).close})
                    trades[-1].update({"active": True})
                    trades[-1].update({"entry_date": prices.get_last_price_date(sec['security'])})
        trades[-1].update({"total_valuation": total_valuation})

    return 1000000, trades


def customized_buy_sell_signal_for_backtest(response, data):
    close = [float(x.close) for x in response]
    high = [float(x.high) for x in response]
    low = [float(x.low) for x in response]
    customized_buy_signal = []
    buy_keys = {}
    customized_sell_signal = []
    sell_keys = {}
    v = VectorbtService()
    for ind, strat in enumerate(data.customized_sell_signal):
        customized_sell_signal.append({strat.security_group: v.get_custom_indicator_signals(response, close, high, low, strat.dict())})
        sell_keys.update({ ind: strat.security_group})

    for ind, strat in enumerate(data.customized_buy_signal):
        customized_buy_signal.append({strat.security_group: v.get_custom_indicator_signals(response, close, high, low, strat.dict())})
        buy_keys.update({ind: strat.security_group})
    return customized_buy_signal, buy_keys, customized_sell_signal, sell_keys

    # df = pd.concat([entries, exits], axis=1)
    # df.columns = ['entries', 'exits']
    # for index, row in df.iterrows():
    #     if row['exit']:
    #         for strat in data.customized_sell_signal:
    #             v.custom_indicator_backtester(response, close, high, low, strat)
    #             _, s_exit = v.get_entries_and_exits()
    #             if s_exit[index]:
    #                 send_slack_alert(f"SELL SIGNAL: {strat}")
    #                 # TODO: buy into portfolio. Also, need to handle multiple buy signals
    #                 break
    #
    #     elif row['entries']:
    #         for strat in data.customized_buy_signal:
    #             v.customized_buy_signal_backtester(response[index], close[index], high[index], low[index], strat)
    #             b_entry, _ = v.get_entries_and_exits()
    #             if b_entry[index]:
    #                 # TODO: sell previous portfolios
    #                 send_slack_alert(f"BUY SIGNAL: {strat}")
    #                 # TODO: buy into portfolio. Also, need to handle multiple sell signals


def format_backtest_input(data):
    input_mapping = {}
    input_mapping['buy'] = []
    input_mapping['sell'] = []
    buy_exp = []
    sell_exp = []
    input_mapping['buy_exp'] = ''
    input_mapping['sell_exp'] = ''
    for i in data['buy']:
        and_exp = ''
        for key, value in i.items():
            input_mapping['buy'].append(
                {
                    key: value
                }
            )
            and_exp += ' & '.join([key])
        buy_exp.append(f'({and_exp})')
    input_mapping['buy_exp'] = ' | '.join(buy_exp)
    for i in data['sell']:
        and_exp = ''
        for key, value in i.items():
            input_mapping['sell'].append(
                {
                    key: value
                }
            )
            and_exp += ' & '.join([key])
        sell_exp.append(f'({and_exp})')
    input_mapping['sell_exp'] = ' | '.join(sell_exp)
    return input_mapping