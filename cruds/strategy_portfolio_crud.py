from typing import List
from schemas.strategy_porfolio_schema import MetricsPortfolio, PaperPorfolio, StrategyGroup, SecurityGroup, \
    SecurityGroupDB
import json


def create_live_portfolio(db, portfolio: MetricsPortfolio):
    data, count = db.table('live_portfolio').insert(json.loads(portfolio.json())).execute()


def insert_paper_metrics(db, portfolio: MetricsPortfolio):
    data, count = db.table('paper_portfolio').insert(json.loads(portfolio.json())).execute()


def get_all_live_portfolio(db, user_id: int, skip: int = 0, limit: int = 100):
    return db.table('live_portfolio').select('*').eq('user_id', user_id).execute().data
    # return {
    #     "data": db.table('backtest').select('*').eq('user_id', user_id).range(skip, limit).execute().data,
    #     "start": limit,
    #     "end": skip,
    #     "count": limit - skip
    # }


def get_all_paper_portfolio(db, user_id: int, skip: int = 0, limit: int = 100):
    return db.table('paper_portfolio').select('*').eq('user_id', user_id).execute().data
    # return {
    #     "data": db.table('backtest').select('*').eq('user_id', user_id).range(skip, limit).execute().data,
    #     "start": limit,
    #     "end": skip,
    #     "count": limit - skip
    # }


def get_live_portfolio(db, user_id: str):
    return db.table('live_portfolio').select('*').eq('user_id', user_id).execute().data


def get_paper_metrics(db, user_id: str, strategy_name: str):
    data = db.table('paper_portfolio').select('*').eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data
    if len(data):
        return data[0]
    return None


def delete_paper_portfolio(db, user_id: int, strategy_name: str):
    return db.table('paper_portfolio').delete().eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data


def delete_live_portfolio(db, user_id: int, strategy_name: str):
    return db.table('live_portfolio').delete().eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data


def update_live_portfolio(db, user_id: str, strategy_name: str, portfolio):
    return db.table('live_portfolio').update(json.loads(portfolio.json()))\
        .eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data


def update_paper_metrics(db, user_id: str, strategy_name: str, portfolio):
    return db.table('paper_portfolio').update(json.loads(portfolio.json()))\
        .eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data


def create_paper_portfolio(db, portfolio: PaperPorfolio):
    data, count = db.table('paper_portfolio').insert(json.loads(portfolio.json())).execute()


def get_paper_portfolio(db, user_id: int):
    return db.table('paper_portfolio').select('*').eq('user_id', user_id).execute().data


def update_paper_portfolio(db, portfolio: PaperPorfolio):
    return db.table('paper_portfolio').update(json.loads(portfolio.json())) \
        .eq('user_id', portfolio.user_id).execute().data


def create_strategy_group(db, strategy_group: StrategyGroup):
    data, count = db.table('strategy_group').insert(json.loads(strategy_group.json())).execute()
    return data


def get_strategy_group(db, id: int):
    return db.table('strategy_group').select('*').eq('id', id).execute().data


def get_all_strategy_groups(db, portfolio: int):
    return db.table('strategy_group').select('*').eq('portfolio', portfolio).execute().data


def update_strategy_group(db, strategy_group: StrategyGroup):
    return db.table('strategy_group').update(json.loads(strategy_group.json())) \
        .eq('portfolio', strategy_group.portfolio).execute().data


def delete_strategy_group(db, id: int):
    return db.table('strategy_group').delete().eq('id', id).execute()


def create_security_group(db, security_group: List[SecurityGroupDB]):
    for i in security_group:
        data, count = db.table('security_group').insert(json.loads(i.json())).execute()


def get_security_group(db, name: str, user_id):
    return db.table('security_group').select('*').eq('user_id', user_id).eq('name', name).execute().data


def get_all_security_groups(db, user_id):
    data = db.table('security_group').select('*').eq('user_id', user_id).execute().data
    res = {}
    for i in data:
        if i['name'] not in res:
            res[i['name']] = []
        res[i['name']].append(SecurityGroup.parse_obj(i))
    return res


def update_security_group(db, security_group: List[SecurityGroup]):
    for i in security_group:
        data, count = db.table('security_group').update(json.loads(i.json())) \
            .eq('name', i.name).execute()


def delete_security_group(db, name: str, user_id):
    return db.table('security_group').delete().eq('user_id', user_id).eq('name', name).execute()