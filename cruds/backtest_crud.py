

def create_backtest(db, backtest):
    data, count = db.table('backtest').insert(backtest).execute()


def get_all_backtest(db, user_id: int, skip: int = 0, limit: int = 100):
    return db.table('backtest').select('*').eq('user_id', user_id).range(skip, limit).execute().data
    # return {
    #     "data": db.table('backtest').select('*').eq('user_id', user_id).range(skip, limit).execute().data,
    #     "start": limit,
    #     "end": skip,
    #     "count": limit - skip
    # }


def get_backtest(db, user_id: str, strategy_name: str):
    data = db.table('backtest').select('*').eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data
    if len(data):
        return data[0]
    return data


def star_backtest(db, strategy_name: str, user_id: int):
    return db.table('backtest').update({
        'strategy_name': strategy_name
    }).eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data


def delete_backtest(db, user_id: int, strategy_name: str):
    return db.table('backtest').delete().eq('user_id', user_id).eq('strategy_name', strategy_name).execute().data

