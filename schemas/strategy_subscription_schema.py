from pydantic import BaseModel


class StrategySubscriptionRequest(BaseModel):
    strategy: str


class StrategySubscription(StrategySubscriptionRequest):
    user_id: str
