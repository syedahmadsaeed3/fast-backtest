from fastapi import HTTPException
from schemas.ticker_schema import Ticker


def create_ticker(db, ticker: Ticker):
    data, count = db.table('ticker').insert(ticker.dict()).execute()
    return data

def bulk_insert_ticker(db, tickers: list):
    try:
        db.table('ticker').insert(tickers).execute()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

def get_all_tickers(db, skip: int = 0, limit: int = 100):
    return {
        "data": db.table('ticker').select('*').range(skip, limit).execute().data,
        "start": limit,
        "end": skip,
        "count": limit-skip
    }

def get_ticker(db, symbol: str):
    data = db.table('ticker').select("*").eq('symbol', symbol).limit(1).execute().data
    if len(data):
        return data[0]
    return data

def search_ticker(db, query: str):
    """
    :param db
    :param query: str
    :return: list

    This function accepts search string and performs full-text search in the database returns the ranked
    results based on the matches

    Reference: https://amitosh.medium.com/full-text-search-fts-with-postgresql-and-sqlalchemy-edc436330a0c
    """
    results = db.table('ticker').select("*").ilike('symbol', f'{query}%').order('symbol').limit(10).execute().data
    if len(results) < 10:
        results += db.table('ticker').select("*").ilike('company_name', f'%{query}%').order('company_name').limit(7).execute().data
    response = []
    for i in results:
        if i not in response:
            response.append(i)

    return response[:11]
