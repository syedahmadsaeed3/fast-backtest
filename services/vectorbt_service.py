import vectorbtpro as vbt
import numpy as np
import pandas as pd
from services.indicator_factory_service import get_indicator
from datetime import datetime


class VectorbtService:

    def __init__(self):
        self.memoized_entries = {}
        self.portfolio = None
        self.entries = {}
        self.exits = {}
        self.total_profit = pd.Series(0)
        self.total_return = pd.Series(0)
        self.max_params = []

    def create_params(self, buy, sell):
        return vbt.utils.params.create_param_product([*buy, *sell])

    def get_entries_and_exits(self, response):
        entries = pd.DataFrame(self.entries)
        exits = pd.DataFrame(self.exits)
        entries.index = [datetime.fromtimestamp(x.timestamp / 1000) for x in response]
        exits.index = [datetime.fromtimestamp(x.timestamp / 1000) for x in response]
        return entries, exits

    def run_portfolio(self, close_list, init_cash):
        entries, exits = self.get_entries_and_exits()
        self.portfolio = vbt.Portfolio.from_signals(close=close_list, entries=entries, exits=exits, init_cash=init_cash,
                                                    freq="1d")
        self.total_profit = self.portfolio.get_total_profit().max()
        self.total_return = self.portfolio.get_total_return().max()
        self.max_params = self.portfolio.get_total_return().idxmax()
        return self.portfolio

    @staticmethod
    def run_custom_portfolio(entries, exits, close_list, init_cash, size, leverage):
        """
        Todo: find a way to use leverage mode in from_signals function
        :param close_list:
        :param init_cash:
        :param size:
        :return:
        """
        leverage = pd.DataFrame(leverage)
        size = pd.DataFrame(size)
        portfolio = vbt.Portfolio.from_signals(close=close_list, entries=entries, exits=exits, init_cash=init_cash,
                                                    freq="1d", size=size, size_type=vbt.pf_enums.SizeType.ValuePercent,
                                                    leverage=leverage)
        return portfolio

    def get_total_profit(self):
        return self.total_profit.max()

    def get_total_return(self):
        return self.total_return.max()

    def get_max_params(self):
        return self.max_params

    def get_max_stats(self):
        return self.portfolio[self.get_max_params()].stats()

    def crossed_above_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_above')(value)

    def crossed_below_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_crossed_below')(value)

    def above_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_above')(value)

    def below_buy_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[0]}_below')(value)

    def crossed_above_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_crossed_above')(value)

    def crossed_below_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_crossed_below')(value)

    def above_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_above')(value)

    def below_sell_trend(self, output_model, indicator, value):
        outputs = output_model.schema()['required']
        return getattr(indicator, f'{outputs[1]}_below')(value)

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

        for ind in indicators["buy"]:
            indicator, data_model, output_model = get_indicator(ind)
            input_mappings = {}
            schema = data_model.schema()['required']

            for s in schema:
                if s != 'close' and s != 'high' and s != 'low' and s != 'aggregates':
                    input_mappings.update({
                        s: args.pop(0)
                    })
            key = ind + str(input_mappings.values())
            if key in self.memoized_entries:
                buy_results.append(self.memoized_entries[key])
                buy_dict[ind] = self.memoized_entries[key]
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
                    if 'close' in output_model.schema()['required']:
                        output_list[0].shape = (len(close_list),)
                        if output_model.schema()['required'][0] == 'close':
                            self.memoized_entries[key] = self.above_buy_trend(output_model, output, output_list[0])
                        else:
                            self.memoized_entries[key] = self.below_buy_trend(output_model, output,
                                                                              np.array(close_list))
                    else:
                        output_list[0].shape = (len(close_list),)
                        output_list[1].shape = (len(close_list),)
                        self.memoized_entries[key] = self.above_buy_trend(output_model, output, output_list[1])
                except:
                    self.memoized_entries[key] = indicator(**parameters)

                buy_results.append(self.memoized_entries[key])
                buy_dict[ind] = self.memoized_entries[key]

        buy_exp = indicators["buy_exp"]
        for b in buy_dict.keys():
            buy_exp = buy_exp.replace(b, f"buy_dict['{b}']")
        entries = eval(buy_exp)

        for ind in indicators["sell"]:
            indicator, data_model, output_model = get_indicator(ind)
            input_mappings = {}
            schema = data_model.schema()['required']

            for s in schema:
                if s != 'close' and s != 'high' and s != 'low' and s != 'aggregates':
                    input_mappings.update({
                        s: args.pop(0)
                    })
            key = ind + str(input_mappings.values())
            if key in self.memoized_entries:
                sell_dict[ind] = self.memoized_entries[key]
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

                    if 'close' in output_model.schema()['required']:
                        output_list[0].shape = (len(close_list),)
                        if output_model.schema()['required'][0] == 'close':
                            self.memoized_entries[key] = self.above_sell_trend(output_model, output,
                                                                               np.array(close_list))
                        else:
                            self.memoized_entries[key] = self.above_buy_trend(output_model, output,
                                                                              np.array(close_list))
                    else:
                        output_list[0].shape = (len(close_list),)
                        output_list[1].shape = (len(close_list),)
                        self.memoized_entries[key] = self.above_sell_trend(output_model, output, output_list[0])
                except:
                    self.memoized_entries[key] = indicator(**parameters)

                sell_results.append(self.memoized_entries[key])
                sell_dict[ind] = self.memoized_entries[key]

        sell_exp = indicators["sell_exp"]
        for b in sell_dict.keys():
            sell_exp = sell_exp.replace(b, f"sell_dict['{b}']")
        exits = eval(sell_exp)

        self.entries[tuple(cols)] = entries
        self.exits[tuple(cols)] = exits
        return

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

        for ind in indicators["buy"]:
            indicator, data_model, output_model = get_indicator(ind)
            input_mappings = indicators['buy'][ind]
            cols += list(input_mappings.values())

            key = ind + str(input_mappings.values())
            if key in self.memoized_entries:
                buy_results.append(self.memoized_entries[key])
                buy_dict[ind] = self.memoized_entries[key]
            else:
                input_mappings.update({"close": close_list})
                input_mappings.update({"high": high}) if "high" in data_model.schema()['properties'].keys() else {}
                input_mappings.update({"low": low}) if "high" in data_model.schema()['properties'].keys() else {}
                input_mappings.update({"aggregates": aggregates}) if "aggregates" in data_model.schema()[
                    'properties'].keys() else {}
                parameters = data_model.parse_obj(input_mappings).dict()
                try:
                    output = indicator.run(**parameters)
                    output_list = output.config['output_list']
                    if 'close' in output_model.schema()['required']:
                        output_list[0].shape = (len(close_list),)
                        if output_model.schema()['required'][0] == 'close':
                            self.memoized_entries[key] = self.above_buy_trend(output_model, output, output_list[0])
                        else:
                            self.memoized_entries[key] = self.below_buy_trend(output_model, output,
                                                                              np.array(close_list))
                    else:
                        output_list[0].shape = (len(close_list),)
                        output_list[1].shape = (len(close_list),)
                        self.memoized_entries[key] = self.above_buy_trend(output_model, output, output_list[1])
                except Exception as e:
                    self.memoized_entries[key] = indicator(**parameters)

                buy_results.append(self.memoized_entries[key])
                buy_dict[ind] = self.memoized_entries[key]

        buy_exp = indicators["buy_exp"]
        for b in buy_dict.keys():
            buy_exp = buy_exp.replace(b, f"buy_dict['{b}']")
        entries = eval(buy_exp)

        for ind in indicators["sell"]:
            indicator, data_model, output_model = get_indicator(ind)
            input_mappings = indicators['sell'][ind]
            cols += list(input_mappings.values())
            key = ind + str(input_mappings.values())
            if key in self.memoized_entries:
                sell_dict[ind] = self.memoized_entries[key]
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
                    output_list = output.config['output_list']

                    if 'close' in output_model.schema()['required']:
                        output_list[0].shape = (len(close_list),)
                        if output_model.schema()['required'][0] == 'close':
                            self.memoized_entries[key] = self.above_sell_trend(output_model, output,
                                                                               np.array(close_list))
                        else:
                            self.memoized_entries[key] = self.above_buy_trend(output_model, output,
                                                                              np.array(close_list))
                    else:
                        output_list[0].shape = (len(close_list),)
                        output_list[1].shape = (len(close_list),)
                        self.memoized_entries[key] = self.above_sell_trend(output_model, output, output_list[0])
                except:
                    self.memoized_entries[key] = indicator(**parameters)

                sell_results.append(self.memoized_entries[key])
                sell_dict[ind] = self.memoized_entries[key]

        sell_exp = indicators["sell_exp"]
        for b in sell_dict.keys():
            sell_exp = sell_exp.replace(b, f"sell_dict['{b}']")
        exits = eval(sell_exp)

        self.entries[tuple(cols)] = entries
        self.exits[tuple(cols)] = exits
        return




















