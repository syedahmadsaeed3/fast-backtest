import requests
from fastapi import HTTPException
from services.helper_classes import PriceCache
from datetime import timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

user_data = {}


def get_orders(order_dates, buy, sell):
    res = []
    for i in range(len(order_dates)):
        if i % 2 == 0:
            res.append({
                "timestamp": str(order_dates[i]).split(" ")[1].split('-')[0],
                "action": "buy",
                "price": f"{buy[i//2]:,.2f}",
                "cash_remaining": 0
            })
        else:
            if len(sell):
                res.append({
                    "timestamp": str(order_dates[i]).split(" ")[1].split('-')[0],
                    "action": "sell",
                    "price": f"{sell[i//2]:,.2f}",
                    "cash_remaining": "1,000,000"
                })
    return res if len(sell) else res[0:1]


def format_data(obj):
    res = {}
    res['name'] = list(obj.keys())[0]
    res.update(obj[res['name']])
    return res


def date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def get_security_group_names(trade):
    return [
        t for t in trade if
        t != f"entry_date" and t != "cash_before_trade" and t != "cash_remaining" and
        t != "total_valuation" and t != "active"
    ]


def normalize_prices(prices):
    divisor = prices[0][0]
    for ind, i in prices.iterrows():
        prices.at[ind, 0] = prices[0][ind] / divisor * 100
    return prices


def normalized_portfolio_shares(trade, security_group, initial_cash, start_date, end_date):
    prices = PriceCache()
    share = []
    close = []
    portfolio_shares = []

    for sec in security_group:
        close.append(prices.get_prices_in_date_range(sec['name'], start_date, end_date))
        share.append(sec['shares'])
    for i in zip(*close):
        total = 0
        for ind, value in enumerate(i):
            total += value.close * share[ind]
        portfolio_shares.append(total)
    return portfolio_shares[:-1] if "active" not in trade else portfolio_shares


def get_portfolio_valuation_list(trades):
    first_trade = trades[0]
    first_ind = 0
    valuation_list = []
    for i in trades[first_ind + 1:]:
        if 'cash' not in first_trade or True:
            valuation_list += normalized_portfolio_shares(i,
                                                          [first_trade[x] for x in first_trade if
                                                           x != 'cash_before_trade' and x != 'cash_remaining'
                                                           and x != 'total_valuation' and x != 'entry_date'],
                                                          first_trade['total_valuation'],
                                                          first_trade['entry_date'], i['entry_date'])
        first_trade = i
    return valuation_list


def cache_price_data(data_service, limit, resolution, security_group):
    prices = PriceCache()
    for b in security_group:
        for security in b:
            if prices.get_price(security['security']) is None:
                sec_close = data_service.get_1min_day_data(security['security'],
                                                           limit=None) if limit == 1 else data_service.get_n_day_data(
                    limit, security['security'])
                prices.set_price(security['security'], sec_close)


def send_slack_alert(message: str):
    """
    TODO: define slack webhook URL
    """
    payload = {"text": message}
    button = {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Link Button"
        },
        "url": "https://api.slack.com/block-kit"
    }

    print(payload)
    response = requests.post("https://hooks.slack.com/services/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",
                             json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send Slack alert")


def send_slack_button(channel, text, button_text, url):
    # Initialize WebClient with your Slack token
    client = WebClient("xoxb-671794650261-6682504946245-xt48cw3qtjVXKyXkfNPMLfDh")

    # Define the block with a button
    block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": button_text
            },
            "url": url
        },
    }

    # Try sending the message
    try:
        response = client.chat_postMessage(
            channel="@ahmad",
            blocks=[block]
        )
        print("Message sent successfully:", response)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")




