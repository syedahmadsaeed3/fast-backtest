# from main import plot_strategy_line
#
# def test_add_strategy_to_graph_data():
#     res = {
#         'graph_data': {
#             'layout': {
#                 'shapes': [
#                     {'x0': 2, 'x1': 4},
#                     {'x0': 6, 'x1': 8}
#                 ]
#             },
#             'data': [
#                 {'x': [1, 2, 3, 4, 5, 6, 7, 8, 9], 'y': [3, 4, 5, 6, 7, 8, 9, 10, 11]}
#             ]
#         }
#     }
#
#     plot_strategy_line(res)
#
#     assert len(res['graph_data']['data']) == 2
#     assert res['graph_data']['data'][1]['name'] == 'Strategy'
#     assert res['graph_data']['data'][1]['type'] == 'scatter'
#     assert res['graph_data']['data'][1]['mode'] == 'line'
#     assert res['graph_data']['data'][1]['line']['color'] == '#ffffff'
#     # assert res['graph_data']['data'][1]['x'] == [1, 2, 4, 6, 8, 9]
#     # assert res['graph_data']['data'][1]['y'] == [3, 4, 4, 4, 7, 8]