from copy import deepcopy
from typing import List, Dict

from schemas.strategy_porfolio_schema import StrategyGroup, SecurityGroup, MetricsPortfolio
import vectorbt as vbt
import numpy as np
import pandas as pd
import re
from services.indicator_factory_service import get_indicator
import datetime


class VectorbtService:

    def __init__(self):
        self.memoized_entries = {}
        self.entries = {}
        self.exits = {}
        self.total_profit = pd.Series(0)
        self.total_return = pd.Series(0)
        self.max_params = []
        self.top_params = []
        self.params_mapping = {}

    def get_params_mapping(self):
        return self.params_mapping

    def create_params(self, buy, sell):
        return vbt.utils.params.create_param_product([*buy, *sell])

    def get_entries_and_exits(self):
        return pd.DataFrame(self.entries), pd.DataFrame(self.exits)

    def update_entries_and_exits(self, entries, exits):
        self.entries = entries
        self.exits = exits

    def init_portfolio(self):
        return vbt.Portfolio.from_signals

    def init_trade_graph(self, close):
        pf = vbt.Portfolio.from_signals(close=close, entries=[False], exits=[False], init_cash=1000000)
        return pf.plot_trades(column=pf.wrapper.columns[0])

    def get_last_entry_and_exit(self):
        entry = {list(self.entries.keys()[-1]): list(self.entries.values()[-1])}
        exit = {self.exits.keys()[-1]: self.exits.values()[-1]}
        return pd.DataFrame(entry), pd.DataFrame(exit)

    def cal_vbt_metrics(self, close_data, buy_signals, sell_signals):
        # Assuming you have price data for AAPL, TSLA, MSFT, and AMD as DataFrames
        # Create a dictionary to hold the price data
        # price_data = {
        #     'AAPL': aapl_close_prices,
        #     'TSLA': tsla_close_prices,
        #     'MSFT': msft_close_prices,
        #     'AMD': amd_close_prices
        # }


        # Initialize the portfolios
        portfolio_1st = vbt.Portfolio.from_holding(close_data, init_cash=1000000)
        portfolio_2nd = vbt.Portfolio.from_holding(close_data, init_cash=1000000)

        # Execute the strategy using from_signal function
        pf = vbt.Portfolio.from_signal(
            portfolio_1st, portfolio_2nd, buy_signals, sell_signals,
            group_labels=['entry_1st_portfolio', 'exit_1st_portfolio', 'entry_2nd_portfolio', 'exit_2nd_portfolio'],
            cash_sharing=True,
            group_by=True
        )

        # Calculate final portfolio values
        stats = pf.stats()
        return stats

    def run_portfolio(self, close_list, init_cash, lookback_size, entries=None, exits=None):
        if not entries or not exits:
            entries, exits = self.get_entries_and_exits()
        # entries = entries[lookback_size:].copy()
        # exits = exits[lookback_size:].copy()
        # close_list = close_list[lookback_size:].copy()
        entries.index = close_list.index
        exits.index = close_list.index
        self.portfolio = vbt.Portfolio.from_signals(close=close_list, entries=entries, upon_long_conflict="Exit",
                                                    exits=exits, init_cash=init_cash, freq="1d")
        self.portfolio.stats()
        self.total_profit = self.portfolio.total_profit().max()
        self.total_return = self.portfolio.total_return().max()
        self.max_params = self.portfolio.total_return().idxmax()
        length = len(self.portfolio.total_return())
        prev = []
        if length > 1:
            pf_list = self.portfolio.total_return().sort_values(ascending=False).head(length)
            top_params = pf_list.index.tolist()
            self.top_params.append(top_params[0])
            prev.append(pf_list[top_params[0]])
            for ind, values in enumerate(zip(top_params, pf_list)):
                if values[1] not in prev:
                    self.top_params.append(values[0])
                    prev.append(values[1])
                if len(self.top_params) == 10:
                    break
        return self.portfolio

    def get_total_profit(self):
        return self.total_profit.max()

    def get_total_return(self):
        return self.total_return.max()

    def get_max_params(self):
        return self.max_params

    def get_top_params(self):
        return self.top_params

    def get_max_stats(self):
        return self.portfolio[self.get_max_params()].stats()

    def get_top_stats(self):
        stats = []
        for param in self.get_top_params():
            stats.append(self.portfolio[param].stats())
        return stats

    def crossed_above_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_above')(value)

    def crossed_below_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_below')(value)

    def above_buy_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.superl.isnull()).vbt.signals.fshift()
        elif 'rsi' in indicator.output_names:
            outputs = output_model.schema()['required']
            return getattr(indicator, f'{outputs[0]}_below')(value)
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_above')(value)

    def below_buy_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.supers.isnull()).vbt.signals.fshift()
        elif 'rsi' in indicator.output_names:
            outputs = output_model.schema()['required']
            return getattr(indicator, f'{outputs[0]}_above')(60)
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_below')(value)

    def crossed_above_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_crossed_above')(value)

    def crossed_below_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_crossed_below')(value)

    def above_sell_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.supers.isnull()).vbt.signals.fshift()
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_above')(value)

    def below_sell_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.superl.isnull()).vbt.signals.fshift()
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_below')(value)

    def crossed_above_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_above')(value)

    def crossed_below_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_below')(value)

    def above_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.superl.isnull()).vbt.signals.fshift()
        elif 'rsi' in indicator.output_names:
            outputs = output_model.schema()['required']
            return getattr(indicator, f'{outputs[0]}_below')(value)
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_above')(value)

    def below_trend(self, output_model, indicator, value):
        if 'supers' in indicator.output_names:
            return (~indicator.supers.isnull()).vbt.signals.fshift()
        elif 'rsi' in indicator.output_names:
            outputs = output_model.schema()['required']
            return getattr(indicator, f'{outputs[0]}_above')(value)
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_below')(value)

    def custom_indicator_optimizer(self, aggregates, close_list, high, low, indicators, args):
        """
        :param close_list: list
        :param high: list
        :param low: list
        :param indicators: dict
        :param args: list
        :return: list(list)
        """
        buy_results = []
        buy_dict = {}
        sell_results = []
        sell_dict = {}
        cols = args.copy()
        self.params_mapping[tuple(cols)] = {}
        self.params_mapping[tuple(cols)]['buy'] = {}
        self.params_mapping[tuple(cols)]['sell'] = {}

        for items in indicators["buy"]:
            for ind, value in items.items():
                indicator, data_model, output_model = get_indicator(ind)
                input_mappings = {}
                schema = data_model.schema()['required']

                for s in schema:
                    if s != 'close' and s != 'high' and s != 'low' and s != 'aggregates':
                        input_mappings.update({
                            s: args.pop(0)
                        })
                if args[0] in ['ABOVE', 'BELOW', 'CROSSED_ABOVE', 'CROSSED_BELOW']:
                    input_mappings.update({
                        'trend': args.pop(0)
                    })
                self.params_mapping[tuple(cols)]['buy'].update({ind: input_mappings.copy()})
                key = ind + "".join([str(x) for x in list(value.values())]) + \
                      "".join([str(x) for x in input_mappings.values()])
                if key in self.memoized_entries:
                    buy_results.append(self.memoized_entries[key])
                    buy_dict[key] = self.memoized_entries[key]
                else:
                    input_mappings.update({"close": close_list})
                    input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                        'properties'].keys() else {}
                    parameters = data_model.parse_obj(input_mappings).dict()
                    try:
                        output = indicator.run(**parameters)
                        output_list = output.config.output_list
                        output_list[0].shape = (len(close_list),)
                        if 'close' not in output_model.schema()['required']:
                            output_list[1].shape = (len(close_list),)
                        reference = output_list[0] if 'reference' not in input_mappings else input_mappings['reference']
                        if input_mappings['trend'].lower() == 'crossed_above':
                            self.memoized_entries[key] = self.crossed_above_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'crossed_below':
                            self.memoized_entries[key] = self.crossed_below_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'above':
                            self.memoized_entries[key] = self.above_trend(output_model, output, reference)
                        else:
                            self.memoized_entries[key] = self.below_trend(output_model, output, reference)
                    except:
                        self.memoized_entries[key] = indicator(**parameters, buy=True)

                    buy_results.append(self.memoized_entries[key])
                    buy_dict[key] = self.memoized_entries[key]

        buy_exp = indicators["buy_exp"]
        for to_replace, to_be_replaced in zip(buy_dict.keys(), re.split(r'&|!', buy_exp.replace('|', '!').replace('(',
                                                                                                                  '').replace(
                ')', ''))):
            buy_exp = buy_exp.replace(to_be_replaced.strip(), f"""buy_dict["{to_replace}"]""")
        entries = eval(buy_exp)

        for items in indicators["sell"]:
            for ind, value in items.items():
                indicator, data_model, output_model = get_indicator(ind)
                input_mappings = {}
                schema = data_model.schema()['required']

                for s in schema:
                    if s != 'close' and s != 'high' and s != 'low' and s != 'aggregates':
                        input_mappings.update({
                            s: args.pop(0)
                        })
                if args[0] in ['ABOVE', 'BELOW', 'CROSSED_ABOVE', 'CROSSED_BELOW']:
                    input_mappings.update({
                        'trend': args.pop(0)
                    })

                self.params_mapping[tuple(cols)]['sell'].update({ind: input_mappings.copy()})
                key = ind + "".join([str(x) for x in list(value.values())]) + \
                      "".join([str(x) for x in input_mappings.values()])
                if key in self.memoized_entries:
                    sell_dict[key] = self.memoized_entries[key]
                    sell_results.append(self.memoized_entries[key])
                else:
                    input_mappings.update({"close": close_list})
                    input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                        'properties'].keys() else {}
                    parameters = data_model.parse_obj(input_mappings).dict()
                    try:

                        output = indicator.run(**parameters)
                        output_list = output.config.output_list

                        output_list[0].shape = (len(close_list),)
                        if 'close' not in output_model.schema()['required']:
                            output_list[1].shape = (len(close_list),)
                        reference = output_list[0] if 'reference' not in input_mappings else input_mappings['reference']
                        if input_mappings['trend'].lower() == 'crossed_above':
                            self.memoized_entries[key] = self.crossed_above_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'crossed_below':
                            self.memoized_entries[key] = self.crossed_below_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'above':
                            self.memoized_entries[key] = self.above_trend(output_model, output, reference)
                        else:
                            self.memoized_entries[key] = self.below_trend(output_model, output, reference)
                    except Exception as e:
                        self.memoized_entries[key] = indicator(**parameters, buy=False)

                    sell_results.append(self.memoized_entries[key])
                    sell_dict[key] = self.memoized_entries[key]

        sell_exp = indicators["sell_exp"]
        for to_replace, to_be_replaced in zip(sell_dict.keys(), re.split(r'&|!', sell_exp.replace('|', '!').replace('(',
                                                                                                                    '').replace(
                ')', ''))):
            sell_exp = sell_exp.replace(to_be_replaced, f"""sell_dict["{to_replace}"]""")
        exits = eval(sell_exp)

        self.entries[tuple(cols)] = entries
        self.exits[tuple(cols)] = exits
        return

    def get_custom_indicator_signals(self, aggregates, close_list, high, low, ind_input):
        """
        :param close_list: list
        :param high: list
        :param low: list
        :param indicators: dict

        :return: list(list)
        """
        results = []
        exp_dict = {}
        cols = []

        """
        TODO: use this contracts list to generate the new close list
        """
        indicators = deepcopy(ind_input)
        for items in indicators["strategy"]:
            for ind, value in list(items.items()):

                indicator, data_model, output_model = get_indicator(ind)
                input_mappings = value
                cols += list(input_mappings.values())

                key = ind + ''.join([str(x) for x in input_mappings.values()])
                if key in self.memoized_entries:
                    results.append(self.memoized_entries[key])
                    exp_dict[key] = self.memoized_entries[key]
                else:
                    input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"close": close_list})
                    input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                        'properties'].keys() else {}
                    parameters = data_model.parse_obj(input_mappings).dict()
                    try:
                        output = indicator.run(**parameters)
                        output_list = output.config[
                            'output_list'] if 'output_list' in output.config else output.config.output_list
                        if 'close' not in output_model.schema()['required']:
                            output_list[1].shape = (len(close_list),)
                        reference = output_list[0] if 'reference' not in input_mappings else input_mappings['reference']
                        if input_mappings['trend'].lower() == 'crossed_above':
                            self.memoized_entries[key] = self.crossed_above_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'crossed_below':
                            self.memoized_entries[key] = self.crossed_below_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'above':
                            self.memoized_entries[key] = self.above_trend(output_model, output, reference)
                        else:
                            self.memoized_entries[key] = self.below_trend(output_model, output, reference)
                    except Exception as e:
                        result = indicator(**parameters)
                        self.memoized_entries[key] = result if len(result) >= 2 else result[0]

                    results.append(self.memoized_entries[key])
                    exp_dict[key] = self.memoized_entries[key]

        exp = indicators["expression"]

        for b in exp_dict.keys():
            pattern = rf"\b{b}\b"
            exp = re.sub(pattern, f"exp_dict['{b}']", exp)

        signals = {}
        final_result = eval(exp)
        # check if eval(exp) is type of ndarray
        if not isinstance(final_result, np.ndarray):
            final_result = final_result.values
            signals[tuple(cols)] = final_result.reshape((len(final_result),))
        else:
            signals[tuple(cols)] = final_result
        return pd.DataFrame(signals)

    def custom_indicator_backtester(self, aggregates, close_list, high, low, indicators):
        """
        :param close_list: list
        :param high: list
        :param low: list
        :param indicators: dict

        :return: list(list)
        """
        buy_results = []
        buy_dict = {}
        sell_results = []
        sell_dict = {}
        cols = []

        """
        TODO: use this contracts list to generate the new close list
        """

        for items in indicators["buy"]:
            for ind, value in list(items.items()):

                indicator, data_model, output_model = get_indicator(ind)
                input_mappings = value
                cols += list(input_mappings.values())

                key = ind + ''.join([str(x) for x in input_mappings.values()])
                if key in self.memoized_entries:
                    buy_results.append(self.memoized_entries[key])
                    buy_dict[key] = self.memoized_entries[key]
                else:
                    input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"close": close_list})
                    input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                        'properties'].keys() else {}
                    parameters = data_model.parse_obj(input_mappings).dict()
                    try:
                        output = indicator.run(**parameters)
                        output_list = output.config[
                            'output_list'] if 'output_list' in output.config else output.config.output_list
                        output_list[0].shape = (len(close_list),)
                        if 'close' not in output_model.schema()['required']:
                            output_list[1].shape = (len(close_list),)
                        reference = output_list[0] if 'reference' not in input_mappings else input_mappings['reference']
                        if input_mappings['trend'].lower() == 'crossed_above':
                            self.memoized_entries[key] = self.crossed_above_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'crossed_below':
                            self.memoized_entries[key] = self.crossed_below_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'above':
                            self.memoized_entries[key] = self.above_trend(output_model, output, reference)
                        else:
                            self.memoized_entries[key] = self.below_trend(output_model, output, reference)

                    except Exception as e:
                        result = indicator(**parameters)
                        self.memoized_entries[key] = result if len(result) >= 2 else result[0]

                    buy_results.append(self.memoized_entries[key])
                    buy_dict[key] = self.memoized_entries[key]

        buy_exp = indicators["buy_exp"]

        for b in buy_dict.keys():
            pattern = rf"\b{b}\b"
            buy_exp = re.sub(pattern, f"buy_dict['{b}']", buy_exp)
        entries = eval(buy_exp)

        for items in indicators["sell"]:
            for ind, value in list(items.items()):
                indicator, data_model, output_model = get_indicator(ind)
                input_mappings = value
                cols += list(input_mappings.values())
                key = ind + ''.join([str(x) for x in input_mappings.values()])
                if key in self.memoized_entries:
                    sell_dict[key] = self.memoized_entries[key]
                    sell_results.append(self.memoized_entries[key])
                else:
                    input_mappings.update({"close": close_list})
                    input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                    input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                        'properties'].keys() else {}
                    parameters = data_model.parse_obj(input_mappings).dict()
                    try:

                        output = indicator.run(**parameters)
                        output_list = output.config[
                            'output_list'] if 'output_list' in output.config else output.config.output_list

                        output_list[0].shape = (len(close_list),)
                        if 'close' not in output_model.schema()['required']:
                            output_list[1].shape = (len(close_list),)
                        reference = output_list[0] if 'reference' not in input_mappings else input_mappings['reference']
                        if input_mappings['trend'].lower() == 'crossed_above':
                            self.memoized_entries[key] = self.crossed_above_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'crossed_below':
                            self.memoized_entries[key] = self.crossed_below_trend(output_model, output, reference)
                        elif input_mappings['trend'].lower() == 'above':
                            self.memoized_entries[key] = self.above_trend(output_model, output, reference)
                        else:
                            self.memoized_entries[key] = self.below_trend(output_model, output, reference)

                    except Exception as e:
                        result = indicator(**parameters)
                        self.memoized_entries[key] = result if len(result) >= 2 else result[1]

                    sell_results.append(self.memoized_entries[key])
                    sell_dict[key] = self.memoized_entries[key]

        sell_exp = indicators["sell_exp"]
        for b in sell_dict.keys():
            pattern = rf"\b{b}\b"
            sell_exp = re.sub(pattern, f"sell_dict['{b}']", sell_exp)
        exits = eval(sell_exp)

        self.entries[tuple(cols)] = entries
        self.exits[tuple(cols)] = exits


class Portfolio():

    owner = None
    cash = None
    strategy = {}

    def __init__(self, owner=None, cash=None, strategy=None):
        self.owner = owner
        self.cash = cash
        self.strategy = strategy

    def print(self):
        print(self.cash)
        print(self.strategy)

    def update_portfolio(self, cash):
        self.cash = cash

    def constructor(self, strategy: StrategyGroup):
        self.strategy[strategy.name] = strategy

    def get_portfolio(self):
        return self.cash

    def get_owner(self):
        return self.owner

    def on_buy_signal(self, name):
        strat = self.strategy[name]
        return {
            "allocation": strat.allocation,
        }




