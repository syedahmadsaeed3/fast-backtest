import uuid
from typing import List
from controllers.auth_manager import JWTBearer
from controllers.data_service_manager import get_data_service
from cruds.backtest_crud import get_backtest
from cruds.strategy_portfolio_crud import get_paper_portfolio, get_live_portfolio, create_strategy_group, create_security_group, \
    get_all_security_groups, get_security_group, delete_security_group
from cruds.strategy_subscription_crud import create_subscription, get_subscription, remove_subscription
from database import get_supabase
from schemas.backtest_schema import Backtest, BacktestResponse
from cruds import backtest_crud
from fastapi import Depends, HTTPException
from fastapi import APIRouter
import json
from schemas.strategy_porfolio_schema import StrategyGroup, SecurityGroup, CreateSecurityGroup
from schemas.strategy_subscription_schema import StrategySubscription, StrategySubscriptionRequest
from services.binance_service import BinanceService
from services.helper_classes import BackgroundProcess, PriceCache
from services.yfinance_service import Yfinance
from services.vectorbt_opensource_service import VectorbtService, Portfolio
from datetime import datetime
import pandas as pd
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from services.custom_indicators import CustomIndicators
from tqdm import tqdm
from cruds.ticker_crud import get_ticker
from services.data_models import data, hypothesis_data, LiveStrategy
from services.helper_classes import UserThread
from services.utils import get_orders, format_data, cache_price_data, normalize_prices
from services.graph import plot_strategy_line, create_trades_graph
from services.stats import get_stats
from services.trades import loop_paper_portfolio, looping_run, run_portfolio, start_backtest, get_trades, \
    customized_buy_sell_signal_for_backtest

router = APIRouter()
threads = {}

@router.post("/save_backtest/")
def save_user_backtest(backtest: Backtest, db=Depends(get_supabase), user=Depends(JWTBearer())):
    try:
        if any(backtest_crud.get_backtest(db, user.id, backtest.strategy_name)):
            raise Exception("strategy_name already exists")
        else:
            backtest = backtest.dict()
            backtest.update({"user_id": user.id})
            backtest_crud.create_backtest(db, backtest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")
    return {"message": "backtest saved successfully"}


@router.put("/star_backtest/{backtest_name}")
def star_single_backtest(backtest_name: str, db=Depends(get_supabase), user=Depends(JWTBearer())):
    """
    TODO: change logic to check pre-existing strategy name
    """
    try:
        backtest_list = backtest_crud.get_all_backtest(db, user.id)
        exists = any(test.strategy_name == backtest_name for test in backtest_list)
        if exists:
            test = backtest_crud.star_backtest(db, backtest_name, user.id)
            return {"message": "backtest star status changed", "status": test}
        else:
            raise {"message": "backtest_name does not exist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")


@router.get("/get_backtests/", response_model=List[BacktestResponse])
def get_user_backtests(db=Depends(get_supabase), user=Depends(JWTBearer())):
    backtest_list = backtest_crud.get_all_backtest(db, user.id)
    res = []
    for i in backtest_list:
        obj = {}
        buy_list = []
        buy_ind_list = i['buy']
        buy_and_list = []
        buy_exp_list = [x for x in i['buy_exp'] if x == '&' or x == '|']
        buy_and_list.append(format_data(buy_ind_list.pop(0)))
        for exp in buy_exp_list:
            if exp == '&':
                buy_and_list.append(format_data(buy_ind_list.pop(0)))
            else:
                buy_list.append(buy_and_list)
                buy_and_list = []
                buy_and_list.append(format_data(buy_ind_list.pop(0)))
        buy_list.append(buy_and_list)

        sell_list = []
        sell_ind_list = i['sell']
        sell_and_list = []
        sell_exp_list = [x for x in i['sell_exp'] if x == '&' or x == '|']
        sell_and_list.append(format_data(sell_ind_list.pop(0)))
        for exp in sell_exp_list:
            if exp == '&':
                sell_and_list.append(format_data(sell_ind_list.pop(0)))
            else:
                sell_list.append(sell_and_list)
                sell_and_list = []
                sell_and_list.append(format_data(sell_ind_list.pop(0)))
        sell_list.append(sell_and_list)

        strat_list = []
        for ind in i['customized_buy_signal']:
            strat_ind_list = ind['strategy']
            strat_and_list = []
            strat_exp_list = [x for x in ind['expression'] if x == '&' or x == '|']
            strat_and_list.append(format_data(strat_ind_list.pop(0)))
            for exp in strat_exp_list:
                if exp == '&':
                    strat_and_list.append(format_data(strat_ind_list.pop(0)))
                else:
                    strat_list.append(buy_and_list)
                    strat_and_list = []
                    strat_and_list.append(format_data(strat_ind_list.pop(0)))
            strat_list.append({"strat": strat_and_list, "security_group": ind['security_group']})

        obj['customized_buy_signal'] = strat_list
        strat_list = []
        for ind in i['customized_sell_signal']:
            strat_ind_list = ind['strategy']
            strat_and_list = []
            strat_exp_list = [x for x in ind['expression'] if x == '&' or x == '|']
            strat_and_list.append(format_data(strat_ind_list.pop(0)))
            for exp in strat_exp_list:
                if exp == '&':
                    strat_and_list.append(format_data(strat_ind_list.pop(0)))
                else:
                    strat_list.append(buy_and_list)
                    strat_and_list = []
                    strat_and_list.append(format_data(strat_ind_list.pop(0)))
            strat_list.append({"strat": strat_and_list, "security_group": ind['security_group']})

        obj['customized_sell_signal'] = strat_list
        obj["buy"] = buy_list
        obj["sell"] = sell_list
        obj['status'] = i['status']
        obj['ticker'] = i['ticker']
        obj['limit'] = i['limit']
        obj['resolution'] = i['resolution']
        obj['type'] = i['type']
        obj["strategy_name"] = i['strategy_name']
        obj["win"] = i['win']
        obj["allocation"] = i['allocation']
        obj["avg_trade"] = i['avg_trade']
        obj["return_perc"] = i['return_perc']
        obj["trades"] = i['trades']
        obj["starred"] = i['starred']

        res.append(obj)

    return res


@router.post("/find_previous_occurences")
async def find_previous_occurences(data: hypothesis_data, user=Depends(JWTBearer())):
    p = Portfolio(data.ticker, data.timeperiod, data.direction)
    p.print()
    try:
        data_service = get_data_service()
    except Exception as e:
        print(e)
        data_service = Yfinance()
    days = 0
    if data.timeperiod <= 15:
        days = 183
    if data.timeperiod <= 30 and data.timeperiod > 15:
        days = 365
    if data.timeperiod > 30:
        days = 1825

    response = data_service.get_n_day_data(days, data.ticker)
    result = CustomIndicators.find_previous_occurences(response, data.direction, data.magnitude, data.timeperiod)
    res = jsonable_encoder(
        {
            "total_occurrences": len(result),
            "ranges": result,
            "close_list": [{"close": response['close'], "time": [datetime.fromtimestamp(x/1000) for x in response['timestamp']]}]
        }
    )
    return JSONResponse(content=res)


@router.post("/save_strategy")
async def save_strategy(strategy: StrategyGroup, db=Depends(get_supabase), user=Depends(JWTBearer())):
    try:
        portfolio = get_paper_portfolio(db, user.id)
        security_group = strategy.dict().pop('security_group')
        strategy.portfolio = portfolio['id']
        obj = create_strategy_group(db, strategy)
        for s in security_group:
            s = SecurityGroup.parse_obj(s)
            s.strategy_id = obj['id']
        create_security_group(db, security_group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {e}")
    return {"message": "backtest saved successfully"}


@router.post("/live_run")
async def run_live(data: LiveStrategy, db=Depends(get_supabase) , user=Depends(JWTBearer())):
    """
    TODO: implement better security logic for storing and retrieving thread ids
    TODO: implement cache for commonly used tickers
    TODO: add ability to select portfolio for base signals
    """
    strategy = Backtest.parse_obj(get_backtest(db, user.id, data.strategy_name))
    if any(strategy):
        ticker = get_ticker(db, strategy.ticker)  # assumes it only runs for single ticker
        if ticker and ticker['is_crypto']:
            data_service = BinanceService()
        else:
            try:
                data_service = get_data_service()
            except Exception as e:
                print(e)
                data_service = Yfinance()

        user_data = UserThread()
        user_data.initialize_user(user.id)
        if not user_data.get_user_data_by_key(user.id, 'slack_webhook'):
            user_data.set_user_data_by_key(user.id, 'slack_webhook', None)

        if not user_data.get_user_data_by_key(user.id, 'portfolio'):
            if data.is_simulated:
                portfolio = get_paper_portfolio(db, user.id)
            else:
                portfolio = get_live_portfolio(db, user.id)
            user_data.set_user_data_by_key(user.id, 'paper_portfolio', portfolio)

        # For now, assuming that the strategy is only for one ticker
        security_group = SecurityGroup.parse_obj({
            "user_id": user.id,
            "name": f"{strategy.ticker}_{strategy.strategy_name}_{user.id}_temp",
            "security": strategy.ticker,
            "allocation": 100,
            "shares": 0,
        })

        if data.subscribe_alert:
            user_profile = db.table('users').select('slack_webhook').eq('id', user.id).execute().data
            if len(user_profile):
                slack_webhook = user_profile[0]['slack_webhook']
                user_data.set_user_data_by_key(user.id, 'slack_webhook', slack_webhook)

        loop_paper_portfolio(data_service, db, strategy, security_group, user.id)
        # thread = BackgroundProcess(target=loop_paper_portfolio, args=[data_service, db, strategy, security_group, user.id])
        # user_data.set_user_data_by_key(user.id, data.strategy_name, thread)
        # thread.start()

        return JSONResponse(content="live started successfully")
    return JSONResponse(content="no strategy found")


@router.post("/unsub_strategy")
async def unsub_strategy(data: StrategySubscriptionRequest, db=Depends(get_supabase), user=Depends(JWTBearer())):
    if user.id not in threads:
        return HTTPException(status_code=400, detail="no live strategy exists for this user")
    if not any(data.strategy in d for d in threads[user.id]):
        return HTTPException(status_code=400, detail=f"no live strategy with name: '{data.strategy}' "
                                                     f"exists for this user")
    obj = [d for d in threads[user.id] if list(d.keys())[0] == data.strategy][0]
    subscription = StrategySubscription.parse_obj({
        "strategy": data.strategy,
        "user_id": user.id
    })
    user_data = UserThread()
    user_data.set_user_data_by_key(user.id, data.strategy, None)
    thread = list(obj.values())[0]
    thread.kill()
    thread.join()
    remove_subscription(db, subscription)
    threads[user.id].remove(obj)
    if not any(threads[user.id]):
        threads.pop(user.id)

    return JSONResponse(content="strategy stopped successfully")


@router.post("/backtest")
async def backtest(data: data, db=Depends(get_supabase)):
    if not any(data.buy) or not any(data.sell):
        raise HTTPException(status_code=400, detail=f"error: Buy and Sell indicators cannot be empty")
    ticker = get_ticker(db, data.ticker)
    if ticker and ticker['is_crypto']:
        data_service = BinanceService()
    else:
        try:
            data_service = get_data_service()
        except Exception as e:
            print(e)
            data_service = Yfinance()

    user_data = UserThread()
    user_data.initialize_user("user.id")
    response = data_service.get_n_day_data(data.limit + 183, data.ticker)
    response_without_lookback = data_service.get_n_day_data(data.limit, data.ticker)

    lookback_size = len(response) - len(response_without_lookback)
    price_cache = PriceCache()
    if not price_cache.get_price(data.ticker):
        price_cache.set_price(data.ticker, response)
    close, high, low, vbt = start_backtest(response, db, data, str(uuid.uuid4()))
    dates = close.index.tolist()
    entries, exits = vbt.get_entries_and_exits()
    # if data.customized_buy_signal and data.customized_sell_signal:
    #     buy_security_group = []
    #     sell_security_group = []
    #     for s in data.customized_buy_signal:
    #         buy_security_group.append(get_security_group(db, s.security_group, "user.id"))
    #     for s in data.customized_sell_signal:
    #         sell_security_group.append(get_security_group(db, s.security_group, "user.id"))
    #
    #     # check if buy and sell security groups have more than 1 security group and if each security group has more than 1 security
    #     normalize = (len(buy_security_group) > 1 or len(sell_security_group) > 1) or (len(
    #         buy_security_group[0]) > 1 or len(sell_security_group[0]) > 1)
    #
    #
    #     user_data.set_user_data_by_key("user.id", 'buy_security_group', buy_security_group)
    #     user_data.set_user_data_by_key("user.id", 'sell_security_group', sell_security_group)
    #     user_data.set_user_data_by_key("user.id", 'cash', 1000000)
    #     customized_buy_signal, buy_keys, customized_sell_signal, sell_keys = customized_buy_sell_signal_for_backtest(
    #         response, data)
    #
    #     cache_price_data(data_service, data.limit, data.resolution, buy_security_group)
    #     cache_price_data(data_service, data.limit, data.resolution, sell_security_group)
    #     init_cash, trades = get_trades(dates, customized_buy_signal, buy_keys, customized_sell_signal, sell_keys,
    #                                    entries, exits, "user.id", lookback_size)
    #     stats = get_stats(trades)
    #     normalized_close = normalize_prices((close[lookback_size:])) if normalize else close[lookback_size:]
    #     graph = create_trades_graph(trades, vbt.init_trade_graph(normalized_close), normalize)
    #     for t in trades:
    #         if t:
    #             t['entry_date'] = str(t['entry_date'])
    #     return JSONResponse(content={"trades": trades, "stats": stats, "graph_data": graph})

    res = run_portfolio(vbt, close, lookback_size)

    return JSONResponse(content=res)


@router.post("/optimize_parameter")
async def optimize_parameter(data: data, db=Depends(get_supabase), user=Depends(JWTBearer())):
    ticker = get_ticker(db, data.ticker)
    if ticker and ticker['is_crypto']:
        data_service = BinanceService()
    else:
        try:
            data_service = get_data_service()
        except Exception as e:
            data_service = Yfinance()
    response = data_service.get_n_day_data(data.days, data.ticker)
    buy = []
    for i in data.buy:
        for j in list(i[list(i.keys())[0]].values()):
            buy.append(j)

    sell = []
    for i in data.sell:
        for j in list(i[list(i.keys())[0]].values()):
            sell.append(j)

    v = VectorbtService()
    params = v.create_params(buy, sell)
    close_list = [float(x.close) for x in response]
    high = [float(x.high) for x in response]
    low = [float(x.low) for x in response]
    for i in tqdm(range(len(params[0]))):
        v.custom_indicator_optimizer(response, close_list, high, low, {"buy": data.buy, "sell": data.sell, "buy_exp": data.buy_exp, "sell_exp": data.sell_exp}, [x[i] for x in params])
    close = pd.DataFrame([float(x.close) for x in response], index=[x.timestamp for x in response])
    pf = v.run_portfolio(close, 1000000)

    response = {}
    response['top_results'] = []
    response['total_combinations'] = len(params[0])
    stats = v.get_top_stats()
    top_params = v.get_top_params()
    params_mapping = v.get_params_mapping()
    for ind, s in enumerate(stats):
        res = {}
        params = top_params[ind]
        res['params'] = params_mapping[params]
        if len(pf.plot_orders(column=params).to_dict()['data']) > 2:
            order_dates = list(pf.plot_orders(column=params).to_dict()['data'][1]['x']) + \
                          list(pf.plot_orders(column=params).to_dict()['data'][2]['x'])
            order_dates.sort()
            buy_order = list(pf.plot_orders(column=params).to_dict()['data'][1]['y'])
            sell_order = list(pf.plot_orders(column=params).to_dict()['data'][2]['y'])
            res['order_details'] = get_orders(order_dates, buy_order, sell_order)
        else:
            res['order_details'] = []
        res['stats'] = json.loads(s.to_json())
        res['stats']['Period'] = str((datetime.fromtimestamp(res['stats']['End'] / 1000) - datetime.fromtimestamp(
            res['stats']['Start'] / 1000)).days) + ' days'
        res['stats']['Start'] = str(datetime.fromtimestamp(res['stats']['Start'] / 1000))
        res['stats']['End'] = str(datetime.fromtimestamp(res['stats']['End'] / 1000))
        res['stats']['Avg Winning Trade Duration'] = str(s['Avg Winning Trade Duration'])
        res['stats']['Avg Losing Trade Duration'] = str(s['Avg Losing Trade Duration'])
        res['stats']['Max Drawdown Duration'] = str(s['Max Drawdown Duration'])
        res['graph_data'] = pf.plot_trades(params)

        if res['graph_data']['layout']['shapes']:
            has_shapes = True
        else:
            has_shapes = False

        res['graph_data'] = json.loads(res['graph_data'].to_json())
        res['graph_data']['data'] = res['graph_data']['data'][:1]
        res['graph_data']['data'][0]['line']['color'] = '#84cc16'
        if has_shapes:
            plot_strategy_line(res['graph_data'])
            highlight_y0 = min(res['graph_data']['data'][0]['y'] + res['graph_data']['data'][-1]['y']) - 3
            highlight_y1 = max(res['graph_data']['data'][0]['y'] + res['graph_data']['data'][-1]['y']) + 3

            for i in res['graph_data']['layout']['shapes']:
                i['fillcolor'] = "#84cc16" if i['fillcolor'] == 'green' else '#f43f5e'
                i['y0'] = highlight_y0
                i['y1'] = highlight_y1

        response['top_results'].append(res)

    return JSONResponse(content=response)


@router.post("/subscribe_strategy")
async def subscribe_strategy(strategy: StrategySubscriptionRequest, db=Depends(get_supabase), user=Depends(JWTBearer())):
    """
    TODO: add logic to retrieve data from db in case server was reset for any reason
    """
    backtest = backtest_crud.get_backtest(db, user.id, strategy.strategy)
    if any(backtest):
        subscription = StrategySubscription.parse_obj({
            "strategy": strategy.strategy,
            "user_id": user.id
        })
        res = get_subscription(db, subscription)
        if any(res):
            raise HTTPException(status_code=400, detail=f"error: strategy already subscribed")
        create_subscription(db, subscription)
        backtest = Backtest.parse_obj(backtest)
        ticker = get_ticker(db, backtest.ticker)

        # TODO: create a separate function to get data from data service
        if ticker and ticker['is_crypto']:
            data_service = BinanceService()
        else:
            try:
                data_service = get_data_service()
            except Exception as e:
                print(e)
                data_service = Yfinance()

        user_data = UserThread()
        user_data.set_user_data_by_key(user.id, 'slack_webhook', None)
        user_profile = db.table('users').select('slack_webhook').eq('id', user.id).execute().data
        if len(user_profile):
            slack_webhook = user_profile[0]['slack_webhook']
            user_data.set_user_data_by_key(user.id, 'slack_webhook', slack_webhook)

        thread = BackgroundProcess(target=looping_run, args=[data_service, db, backtest, user.id])
        if user.id not in threads:
            threads[user.id] = []
        threads[user.id].append({strategy.strategy: thread})
        thread.start()

        return JSONResponse(content="Strategy subscribed successfully")
    return JSONResponse(content="No strategy found")


@router.get("/get_security_groups")
async def get_security_groups(db=Depends(get_supabase), user=Depends(JWTBearer())):
    return get_all_security_groups(db, user.id)


@router.post("/create_security_group")
async def create_user_security_group(groups: CreateSecurityGroup, db=Depends(get_supabase), user=Depends(JWTBearer())):
    if any(get_security_group(db, groups.name, user.id)):
        raise HTTPException(status_code=400, detail=f"error: group name already exists")
    name = groups.name
    groups = groups.security_group_list
    for group in groups:
        group.user_id = user.id
        group.name = name
    try:
        create_security_group(db, groups)
        return JSONResponse(content="Security group created successfully")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"error: {e}")


@router.get("/get_security_group/{name}")
async def get_security_group_by_name(name, db=Depends(get_supabase), user=Depends(JWTBearer())):
    return get_security_group(db, name, user.id)


@router.delete("/delete_security_group/{name}")
async def delete_security_group_by_name(name, db=Depends(get_supabase), user=Depends(JWTBearer())):
    return delete_security_group(db, name, user.id)
