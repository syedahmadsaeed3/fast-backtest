from schemas.strategy_subscription_schema import StrategySubscription


def create_subscription(db, subscription: StrategySubscription):
    data, count = db.table('strategy_subscription').insert(subscription.dict()).execute()
    return data


def remove_subscription(db, subscription: StrategySubscription):
    return db.table('strategy_subscription').delete().eq('user_id', subscription.user_id)\
        .eq('strategy', subscription.strategy).execute()


def get_subscription(db, subscription: StrategySubscription):
    return db.table('strategy_subscription').select('*').eq('user_id', subscription.user_id)\
        .eq('strategy', subscription.strategy).execute().data
