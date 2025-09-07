from datetime import date
import operator
from thetadata import ThetaClient, OptionRight
from typing import Union
from services.options_models import OptionStrategy, OptionContract, Moneyness
from services.thetadata_service import ThetadataService
from datetime import datetime, timezone, timedelta
import QuantLib as ql


def find_option_contract(optionStrategy: OptionStrategy, time: Union[date, datetime], underlying_price) -> OptionContract:
    target_expiry = time + timedelta(days=optionStrategy.DTE)
    expiry = optionStrategy.expirations.loc[optionStrategy.expirations.dt.date.ge(datetime.date(target_expiry))].iloc[0].to_pydatetime()
    if ((optionStrategy.Right is OptionRight.CALL and optionStrategy.Moneyness is Moneyness.OTM)
            or (optionStrategy.Right is OptionRight.PUT and optionStrategy.Moneyness is Moneyness.ITM)):
        shift = operator.add
    else:
        shift = operator.sub
    target_strike = shift(underlying_price, underlying_price * optionStrategy.PctFromMktPrice)
    client = ThetaClient()
    with client.connect():
        strikes = client.get_strikes(optionStrategy.Underlying, expiry)
        strike = strikes.loc[strikes.ge(target_strike)].iloc[0]
        option_contract = OptionContract(
            Underlying=optionStrategy.Underlying,
            Right=optionStrategy.Right,
            StrikePrice=strike,
            Expiry=expiry
        )
    data = option_contract.dict()
    return data

def get_ideal_options(
    ticker: str, # AAPL
    target_date: str, # "YYYY-MM-DD"
    magnitude: str, # "5" for 5%
    direction: str, # "up", "down"
    ):

    current_date_time = datetime.now(timezone.utc)
    today_string = current_date_time.strftime("%Y-%m-%d")
    today_datetime = datetime.strptime(today_string, "%Y-%m-%d")
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
    if target_datetime <= today_datetime:
        return (422, "Error, target date is not in the future")

    return find_highest_return_options(ticker, target_date, magnitude, direction)


def calculate_earliest_viable_dte_options(options_quotes, target_date_string):
    filtered_quotes = []
    target_datetime = datetime.strptime(target_date_string, "%Y-%m-%d")
    for quote in options_quotes:
        if datetime.strptime(quote["expirDate"], "%Y-%m-%d") >= target_datetime:
            filtered_quotes.append(quote)
    return filtered_quotes


def find_highest_return_options(ticker, target_date_string, magnitude, direction):
    list_of_options = []
    list_of_options_on_expiry = []
    highest_return = 0
    on_expiry_highest_return = 0
    target_date = datetime.strptime(target_date_string, "%Y-%m-%d")

    if direction == "down":
        magnitude = - float(magnitude)
    target_increase = float(magnitude) / 100

    thetadata = ThetadataService()
    client = thetadata.get_client_connection()
    with client:
        underlying_data = thetadata.get_stock_at_time(ticker, target_date).to_dict()
        price = underlying_data[list(underlying_data.keys())[3]]
        expirations = client.get_expirations(ticker)
        expiries_after_target_date = [x for x in expirations if x > target_date]
        selected_expiry = expiries_after_target_date[2] if len(expiries_after_target_date) > 2 else \
        expiries_after_target_date[1]
        strikes = client.get_strikes(ticker, selected_expiry)
        closest_strikes = select_3_closest_to_strike(strikes, price)
        options = []
        for s in closest_strikes:
            options.append(client.get_opt_at_time(ticker, selected_expiry, s))
    for single_option in closest_strikes:
        strike = single_option["strike"]
        spot = single_option["stockPrice"]
        q = 0  # Dividend rate
        r = .04329  # 3 month treasury risk free rate

        expiry_date = datetime.strptime(single_option["expirDate"], "%Y-%m-%d")
        print(expiry_date)
        dte_on_target_date = (expiry_date - target_date).days
        time_at_expiry = dte_on_target_date / 365

        vol = single_option["callMidIv"]

        dte = single_option["dte"]
        expiry = single_option["expirDate"]

        initial_call_value = single_option["callAskPrice"] if single_option["callAskPrice"] != 0 else 0.01

        t = (dte) / 365
        calculated_initial_call_value = bjerkCall(strike, spot, q, r, t, vol)

        spot_on_expiry = spot * (1 + target_increase)

        calculated_expiry_value = bjerkCall(strike, spot_on_expiry, q, r, time_at_expiry, vol)

        calculated_value_at_expiry = calculated_expiry_value

        return_pct_for_trade = (calculated_expiry_value - calculated_initial_call_value) / calculated_initial_call_value

        risk_reward = calculated_expiry_value / calculated_initial_call_value
        expiry_value = float("%.2f" % calculated_expiry_value)

        stock_price = single_option["stockPrice"]
        moneyness_percentage = ((strike - stock_price) * 100) / stock_price

        if direction == "up":
            if moneyness_percentage > 0:
                moneyness_type = "OTM"
            else:
                moneyness_type = "ITM"
            option_type = "call"
            ask_value = single_option["callAskPrice"]
        else:
            if moneyness_percentage < 0:
                moneyness_type = "OTM"
            else:
                moneyness_type = "ITM"
            option_type = "put"
            ask_value = single_option["putAskPrice"]

        total_cost = float(ask_value) * 100

        risk_reward_one_decimal = "%.1f" % risk_reward
        risk_reward_string = f"1:{risk_reward_one_decimal}"

        moneyness_value_string = "%.1f" % moneyness_percentage
        normalized_moneyness_value_string = abs(float(moneyness_value_string))

        if expiry_date == target_date:
            list_of_options_on_expiry.append({
                'cost': total_cost,
                'ask': ask_value,
                'moneynessType': moneyness_type,
                'moneynessValuePct': normalized_moneyness_value_string,
                'strike': float(strike),
                'stockPrice': stock_price,
                'optionType': option_type,
                'expiry': expiry,
                'estimatedGain': float("%.0f" % (highest_return * 100)),
                'riskReward': risk_reward_string,
                'calculatedValueAtExpiry': expiry_value
            })
            if return_pct_for_trade > on_expiry_highest_return:
                print("HIGHER RETURN PCT THAN ON EXPIRY HIGHEST")
                on_expiry_highest_return = return_pct_for_trade

    filtered_options = []  # need to filter out options that are too far out of the money
    for single_option in filtered_options:
        strike = single_option["strike"]
        spot = single_option["stockPrice"]
        dividend_rate = 0  # Dividend rate
        risk_free_rate = .04329  # 3 month treasury risk free rate

        expiry_date = datetime.strptime(single_option["expirDate"], "%Y-%m-%d")
        if expiry_date < target_date:
            continue
        dte_on_target_date = (expiry_date - target_date).days
        time_at_expiry = dte_on_target_date / 365

        vol = single_option["callMidIv"]

        dte = single_option["dte"]
        expiry = single_option["expirDate"]

        initial_call_value = single_option["callAskPrice"] if single_option["callAskPrice"] != 0 else 0.0111
        print("initial_call_value")
        print(initial_call_value)

        time = (dte) / 365
        calculated_initial_call_value = bjerkCall(strike, spot, dividend_rate, risk_free_rate, time, vol)
        print("calculated_initial_call_value")
        print(calculated_initial_call_value)

        spot_on_expiry = spot * (1 + target_increase)
        calculated_expiry_value = bjerkCall(strike, spot_on_expiry, dividend_rate, risk_free_rate, time_at_expiry, vol)
        print("calculated_expiry_value")
        print(calculated_expiry_value)
        calculated_value_at_expiry = calculated_expiry_value

        return_pct_for_trade = (calculated_expiry_value - initial_call_value) / initial_call_value

        risk_reward = calculated_expiry_value / initial_call_value
        expiry_value = float("%.2f" % calculated_expiry_value)

        stock_price = single_option["stockPrice"]
        moneyness_percentage = ((strike - stock_price) * 100) / stock_price

        if direction == "up":
            if moneyness_percentage > 0:
                moneyness_type = "OTM"
            else:
                moneyness_type = "ITM"
            option_type = "call"
            ask_value = single_option["callAskPrice"]
        else:
            if moneyness_percentage < 0:
                moneyness_type = "OTM"
            else:
                moneyness_type = "ITM"
            option_type = "put"
            ask_value = single_option["putAskPrice"]

        total_cost = float(ask_value) * 100

        risk_reward_one_decimal = "%.1f" % risk_reward
        risk_reward_string = f"1:{risk_reward_one_decimal}"

        moneyness_value_string = "%.1f" % moneyness_percentage
        normalized_moneyness_value_string = abs(float(moneyness_value_string))

        if return_pct_for_trade > highest_return:
            highest_return = return_pct_for_trade
            list_of_options.append({
                'debug': {
                    'dte': dte,
                    'strike': strike,
                    'initial_spot': spot,
                    'spot_on_expiry': spot_on_expiry,
                    'dividend_rate': dividend_rate,
                    'risk_free_rate': risk_free_rate,
                    'time_at_expiry': time_at_expiry,
                    'vol': vol,
                    'initial_real_option_value': initial_call_value,
                    'option_value_at_expiry': calculated_expiry_value
                },
                'strike': float(strike),
                'stockPrice': stock_price,
                'optionType': option_type,
                'cost': total_cost,
                'ask': ask_value,
                'moneynessType': moneyness_type,
                'moneynessValuePct': normalized_moneyness_value_string,
                'expiry': expiry,
                'estimatedGain': float("%.0f" % (highest_return * 100)),
                'riskReward': risk_reward_string,
                'calculatedValueAtExpiry': expiry_value
            })

def select_3_closest_to_strike(strikes, value):
    closest_to_key = min(strikes, key=lambda x:abs(x-value))
    strikes.sort()
    return [strikes[strikes.index(closest_to_key) - 1], closest_to_key, strikes[strikes.index(closest_to_key) + 1]]


import matplotlib.pyplot as plt
import numpy as np
plt.style.use('ggplot')
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.titlesize'] = 18
plt.rcParams['figure.titleweight'] = 'medium'
plt.rcParams['lines.linewidth'] = 2.5

def long_put(S, K, Price):
    # Long Put Payoff = max(Strike Price - Stock Price, 0)     # If we are long a call, we would only elect to call if the current stock price is less than     # the strike price on our option
    P = list(map(lambda x: max(K - x, 0) - Price, S))
    return P

def long_call(S, K, Price):
    # Long Call Payoff = max(Stock Price - Strike Price, 0)     # If we are long a call, we would only elect to call if the current stock price is greater than     # the strike price on our option
    # P = list(map(lambda x: max(x - K, 0) - Price, S))
    # return P
    pass

def short_call(S, K, Price):
    # Payoff a shortcall is just the inverse of the payoff of a long call
    P = long_call(S, K, Price)
    return [-1.0 * p for p in P]

def short_put(S, K, Price):
    # Payoff a short put is just the inverse of the payoff of a long put
    P = long_put(S, K, Price)
    return [-1.0 * p for p in P]

def binary_call(S, K, Price):
    # Payoff of a binary call is either:     # 1. Strike if current price > strike     # 2. 0
    P = list(map(lambda x: K - Price if x > K else 0 - Price, S))
    return P

def binary_put(S, K, Price):
    # Payoff of a binary call is either:     # 1. Strike if current price < strike     # 2. 0
    P = list(map(lambda x: K - Price if x < K else 0 - Price, S))
    return P

from scipy.stats import norm

# S: underlying stock price # K: Option strike price # r: risk free rate # D: dividend value # vol: Volatility # T: time to expiry (assumed that we're measuring from t=0 to T)
def d1_calc(S, K, r, vol, T, t):
    # Calculates d1 in the BSM equation
    return (np.log(S / K) + (r + 0.5 * vol ** 2) * (T - t)) / (vol * np.sqrt(T - t))

# S: underlying stock price # K: Option strike price # r: risk free rate # D: dividend value # vol: Volatility # T: time to expiry (assumed that we're measuring from t=0 to T)
def BS_call(S, K, r, vol, T, t):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def BS_put(S, K, r, vol, T, t):
    return BS_call(S, K, r, vol, T, t) - S + np.exp(-r * (T - t)) * K

def BS_binary_call(S, K, r, vol, T, t):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T - t)
    return np.exp(-r * T) * norm.cdf(d2)

def BS_binary_put(S, K, r, vol, T, t):
    return BS_binary_call(S, K, r, vol, T, t) - S + np.exp(-r * (T - t)) * K

########################################################################### #1st Order Greeks
def delta(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T - t)

    if (otype == "call"):
        delta = np.exp(-(T - t)) * norm.cdf(d1)
    elif (otype == "put"):
        delta = -np.exp(-(T - t)) * norm.cdf(-d1)

    return delta

# Gamma for calls/puts the same
def vega(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    return S * norm.pdf(d1) * np.sqrt(T - t)

def rho(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T - t)

    if (otype == "call"):
        rho = K * (T - t) * np.exp(-r * (T - t)) * norm.cdf(d2)
    elif (otype == "put"):
        rho = -K * (T - t) * np.exp(-r * (T - t)) * norm.cdf(-d2)
    return rho

def theta(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T - t)

    if (otype == "call"):
        theta = -(S * norm.pdf(d1) * vol / (2 * np.sqrt(T - t))) - r * K * np.exp(-r * (T - t)) * norm.cdf(d2)
    elif (otype == "put"):
        theta = -(S * norm.pdf(d1) * vol / (2 * np.sqrt(T - t))) + r * K * np.exp(-r * (T - t)) * norm.cdf(-d2)

    return theta

# 2nd Order Greeks
def gamma(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    gamma = (norm.pdf(d1)) / (S * vol * np.sqrt(T - t))

    return gamma

def charm(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T - t)
    charm = -norm.pdf(d1) * (2 * r * (T - t) - d2 * vol * np.sqrt(T - t)) / (2 * (T - t) * vol * np.sqrt(T - t))

    return charm


def bjerkStens(option_type, strike, spot, q, r, t, vol):
  spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
  today = ql.Date.todaysDate()
  calendar = ql.NullCalendar()
  day_count = int(t *360 + 0.5)
  exDate = today + day_count
  dc = ql.Actual360()
  payoff = ql.PlainVanillaPayoff(option_type, strike)
  flat_ts = ql.YieldTermStructureHandle(ql.FlatForward(today, r, dc))
  dividend_yield = ql.YieldTermStructureHandle(ql.FlatForward(today, q, dc))
  flat_vol_ts = ql.BlackVolTermStructureHandle(
      ql.BlackConstantVol(today, calendar, vol, dc)
  )
  bsm_process = ql.BlackScholesMertonProcess(spot_handle,
                                             dividend_yield,
                                             flat_ts,
                                             flat_vol_ts)
  eng = ql.BjerksundStenslandApproximationEngine(bsm_process)
  payoff = ql.PlainVanillaPayoff(option_type, strike)
  am_exercise = ql.AmericanExercise(today, exDate)
  american_option = ql.VanillaOption(payoff, am_exercise)
  american_option.setPricingEngine(eng)
  return american_option.NPV()

def bjerkCall(strike, spot, q, r, t, vol):
    return bjerkStens(ql.Option.Call, strike, spot, q, r, t, vol)

def bjerkPut(strike, spot, q, r, t, vol):
    return bjerkStens(ql.Option.Put, strike, spot, q, r, t, vol)











