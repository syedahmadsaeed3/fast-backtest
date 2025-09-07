import pytest
from fastapi.testclient import TestClient

from database import supabase
from main import web_app

client = TestClient(web_app)

@pytest.fixture
def mock_data1():
    data = {
        "buy": [{
                "MA":{
                "timeperiod": 14
            }}
        ],
        "sell": [
            {"HEIKEN_ASHI":{
                "candle_number": 3,
                "candle_state": "bearish"
            }}
        ],
        "buy_exp": "(MA14)",
        "sell_exp": "HEIKEN_ASHI3bearish",
        "ticker": "AAPL",
        "customized_buy_signal": [{
            "strategy": [{
                "MA":{
                "timeperiod": 14
            }}],
            "expression": "MA14",
            "security_group": "AAPL"
        }],
        "customized_sell_signal": [{
            "strategy": [{
                "HEIKEN_ASHI":{
                "candle_number": 3,
                "candle_state": "bearish"
            }}],
            "expression": "HEIKEN_ASHI3bearish",
            "security_group": "cash"
        }],
        "limit": 100,
        "resolution": "1d"
    }
    return data


@pytest.fixture
def mock_data2():
    data = {
        "buy": [{
                "MA":{
                "timeperiod": 14
            }}
        ],
        "sell": [
            {"HEIKEN_ASHI":{
                "candle_number": 3,
                "candle_state": "bearish"
            }}
        ],
        "buy_exp": "(MA14)",
        "sell_exp": "HEIKEN_ASHI3bearish",
        "ticker": "AAPL",
        "limit": 100,
        "resolution": "1d"
    }
    return data


def test_customized_backtest(mock_data1, mock_data2):
    token = supabase.auth.sign_in_with_password({"email": "ahmad@iiinigence.com",
                                                 "password": "dc5800SFF"}).session.access_token

    response = client.post("/backtest", json=mock_data1, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    vectorbt_result = response.json()

    response = client.post("/backtest", json=mock_data2, headers={"Authorization": f"Bearer {token}"})
    response_data = response.json()

    assert response.status_code == 200
    assert round(float(response_data['stats']['Total Return [%]']),2) == round(float(vectorbt_result['stats']['Total Return [%]']),2)
    assert round(float(response_data['stats']['Win Rate [%]']),2) == round(float(vectorbt_result['stats']['Win Rate [%]']),2)
    # assert round(float(response_data['stats']['Max Drawdown [%]']),2) == round(float(vectorbt_result['stats']['Max Drawdown [%]']),2)
    # assert response_data['graph_data'] == vectorbt_result['graph_data']

