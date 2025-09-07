import uuid
from schemas.portfolio_schema import Portfolio as schema, Order


def create_portfolio(db, portfolio: schema):
    data, count = db.table('portfolio').insert(portfolio.dict()).execute()
    return data


def get_all_portfolios(db, user_id: uuid, skip: int = 0, limit: int = 100):
    return {
        "data": db.table('portfolio').select('*').eq('owner', user_id).range(skip, limit).execute().data,
        "start": limit,
        "end": skip,
        "count": limit - skip
    }


def delete_portfolio(db, user_id: int, portfolio_name: str):
    db.table('portfolio').delete().eq('owner', user_id).eq('portfolio_name', portfolio_name).execute()


def update_existing_portfolio(db, user_id: int, portfolio: schema, portfolio_name: str):
    return db.table('portfolio').update(portfolio.dict()).eq('owner', user_id).eq('portfolio_name', portfolio_name)\
        .execute()

def create_order(db, order: Order):
    data, count = db.table('orders').insert({
        **order.dict()
    }).execute()
    return data

def get_orders(db, user_id: uuid):
    return db.table('orders').select('*').eq('user_id', user_id).execute().data
