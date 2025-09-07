import json
import operator

import numpy as np
from plotly import graph_objects as go, io as pio

from services.utils import normalized_portfolio_shares


def plot_supertrend(self,
         column=None,
         close_kwargs=None,
         superl_kwargs=None,
         supers_kwargs=None,
         fig=None,
         **layout_kwargs):
    close_kwargs = close_kwargs if close_kwargs else {}
    superl_kwargs = superl_kwargs if superl_kwargs else {}
    supers_kwargs = supers_kwargs if supers_kwargs else {}

    close = self.select_col_from_obj(self.close, column).rename('Close')
    supers = self.select_col_from_obj(self.supers, column).rename('Short')
    superl = self.select_col_from_obj(self.superl, column).rename('Long')

    fig = close.vbt.plot(fig=fig, **close_kwargs, **layout_kwargs)
    supers.vbt.plot(fig=fig, **supers_kwargs)
    superl.vbt.plot(fig=fig, **superl_kwargs)

    return fig


def plot_strategy_line(res):
    res['layout']['shapes'].sort(key=operator.itemgetter('x0'))

    strategy_x = [res['data'][0]['x'][0]]
    strategy_y = [res['data'][0]['y'][0]]

    for i in res['layout']['shapes']:
        strategy_x.append(i['x0'])
        strategy_y.append(strategy_y[-1])
        start_index = res['data'][0]['x'].index(i['x0'])
        difference = res['data'][0]['y'][start_index] - strategy_y[-1]
        while res['data'][0]['x'][start_index] != i['x1']:
            start_index += 1
            strategy_x.append(str(res['data'][0]['x'][start_index]))
            strategy_y.append(res['data'][0]['y'][start_index] - difference)

    res['data'].append({
        "line": {
            "color": "#ffffff"
        },
        "mode": "lines",
        "name": "Strategy",
        "x": strategy_x,
        "y": strategy_y,
        "type": "scatter",
    })
    return res


def get_scatter_hover_text(trade):
    if "cash" not in trade:
        template = f'Entry Timestamp: {trade["entry_date"]}<br>Direction: Long'
        # add cash before trade, cash remaining, and total valuation
        template += f'<br>Cash before trade: ${round(trade["cash_before_trade"], 3)}'
        template += f'<br>Cash remaining: ${round(trade["cash_remaining"], 3)}'
        template += f'<br>Total valuation: ${round(trade["total_valuation"], 3)}<br>'

        for t in trade:
            if t != f"entry_date" and t != "cash_before_trade" and t != "cash_remaining" and t != "total_valuation" and t != "active":
                template += f'<br>{t} shares: {trade[t]["shares"]}'
                template += f'<br>{t} price: ${round(trade[t]["price"], 3)}'
                template += f'<br>{t} total: ${round(trade[t]["total"], 3)}'
                template += f'<br>'
    else:
        template = f'Exit Timestamp: {trade["entry_date"]}<br>Direction: Long'
        # add cash before trade, cash remaining, and total valuation
        template += f'<br>Cash: ${round(trade["cash"], 3)}'

    return template


def get_marker_details(name):
    color = 'orange'
    if name == "Entry":
        color = 'blue'
    elif name == "Exit Profit":
        color = 'green'
    elif name == "Exit Loss":
        color = 'red'
    return {
        "color": color,
        "size": 6,
        "line": {
            "color": color,
            "width": 1
        },
        "symbol": "square"
    }


def create_trades_graph(trades, graph, normalize):
    """
    TODO: logic to loop security groups and get normalized values
    """
    first_trade = None
    first_ind = 0
    graph.data[0].line.color = "#84cc16"
    for ind, x in enumerate(trades):
        if x:
            first_trade = x
            first_ind = ind
            break

    strat_y = [graph.data[0].y[np.where(first_trade['entry_date']==graph.data[0].x)][0]]
    strat_x = [first_trade['entry_date']]
    valuation_list = []
    normalized_portfolio_close = []
    if normalize:
        for i in trades[first_ind + 1:]:
            if 'cash' not in first_trade:
                valuation_list += normalized_portfolio_shares(i,
                                                              [first_trade[x] for x in first_trade if x != 'cash_before_trade' and x != 'cash_remaining'
                                                               and x != 'total_valuation' and x != 'entry_date'], first_trade['total_valuation'],
                                                              first_trade['entry_date'], i['entry_date'])
            first_trade = i
        for i in valuation_list:
            normalized_portfolio_close.append(i/valuation_list[0]*100)

    first_trade = trades[first_ind]


    graph.add_trace(go.Scatter(
        x=(first_trade['entry_date'],),
        y=(strat_y[0],),
        mode='markers',
        name="Entry",
        hovertemplate=get_scatter_hover_text(first_trade),
        marker=get_marker_details("Entry"),
        showlegend=False
    ))

    for ind, trade in enumerate(trades[first_ind + 1:]):
        if trade and first_trade:
            if first_trade['total_valuation'] < trade['total_valuation']:
                color = "#84cc16"
            else:
                color = "#f43f5e"

            if 'cash' not in first_trade:
                graph.add_shape(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=first_trade['entry_date'],
                    y0=min(graph.data[0].y),
                    x1=trade['entry_date'],
                    y1=max(graph.data[0].y),
                    fillcolor=color,
                    # add border color

                    opacity=0.2,
                    layer="below",
                    line=dict(width=1, color=color)
                )
            else:
                if normalize:
                    # loop through graph.data[0].x from first_trade['entry_date'] to trade['entry_date'] and append last strat_y value to strat_y
                    for i in graph.data[0].x:
                        if i >= first_trade['entry_date'] and i < trade['entry_date']:
                            strat_y.append(strat_y[-1])
                        if i > trade['entry_date']:
                            break
            marker = "Entry" if 'cash' not in trade else ("Exit Profit" if color == "#84cc16" else "Exit Loss")
            first_trade = trade
            # add trace in graph
            graph.add_trace(go.Scatter(
                x=(trade['entry_date'],),
                y=(graph.data[0].y[np.where(graph.data[0].x==trade['entry_date'])][0],),
                mode='markers',
                name="",
                hovertemplate=get_scatter_hover_text(trade),
                marker=get_marker_details(marker),
                legendgroup=marker,
                legendgrouptitle=dict(text=marker),
                showlegend=False
            ))

    if not normalize:
        graph = pio.from_json(json.dumps(plot_strategy_line(json.loads(graph.to_json()))))
        strat_y = graph.data[-1].y
    else:
        strat_y = normalized_portfolio_close

    y0_hight = min(strat_y)
    y1_hight = max(strat_y)

    if normalize:
        graph.add_trace(go.Scatter(x=graph.data[0].x, y=strat_y, mode='lines', name='Strategy', line=dict(color='#ffffff'),
                                   opacity=1))
    for x in graph.layout.shapes:
        x.y0 = min(x.y0, y0_hight)
        x.y1 = max(x.y1, y1_hight)
    # graph.show()
    graph_data = json.loads(graph.to_json())
    return graph_data