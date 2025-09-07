def create_backtest(db, backtest):
    data, count = db.table('user_activity_backtest').insert(backtest).execute()
    return data


def get_all_backtest(db, user_id: int, skip: int = 0, limit: int = 100):
    return {
        "data": db.table('user_activity_backtest').select('*').eq('user_id', user_id).range(skip, limit).execute().data,
        "start": limit,
        "end": skip,
        "count": limit - skip
    }

