# import unittest
# import numpy as np
# import pandas as pd
# from .services.custom_indicators import CustomIndicators
# import vectorbt as vbt
#
# class TestCustomIndicators(unittest.TestCase):
#
#     def test_get_final_bands(self):
#         close = np.array([1, 2, 3, 4, 5])
#         upper = np.array([4, 5, 6, 7, 8])
#         lower = np.array([2, 3, 4, 5, 6])
#
#         trend, dir_, long, short = CustomIndicators.get_final_bands(close, upper, lower)
#
#         self.assertIsInstance(trend, np.ndarray)
#         self.assertIsInstance(dir_, np.ndarray)
#         self.assertIsInstance(long, pd.Series)
#         self.assertIsInstance(short, pd.Series)
#         self.assertEqual(trend.shape, close.shape)
#         self.assertEqual(dir_.shape, close.shape)
#         self.assertEqual(long.shape, close.shape)
#         self.assertEqual(short.shape, close.shape)
#
#     def test_get_basic_bands(self):
#         med_price = np.array([1, 2, 3, 4, 5])
#         atr = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
#         multiplier = 2
#
#         upper, lower = CustomIndicators.get_basic_bands(med_price, atr, multiplier)
#
#         self.assertIsInstance(upper, np.ndarray)
#         self.assertIsInstance(lower, np.ndarray)
#         self.assertEqual(upper.shape, med_price.shape)
#         self.assertEqual(lower.shape, med_price.shape)
#
#     def test_super_trend_return_values(self):
#         close = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
#         high = np.array([5.0, 6.0, 7.0, 8.0, 9.0])
#         low = np.array([1.0, 2.0, 3.0, 4.0, 5.0
#                         ])
#         period = 14
#         multiplier = 2
#         buy = True
#
#         entries = CustomIndicators.super_trend_return_values(close, high, low, period, multiplier, buy)
#         self.assertIsInstance(entries, pd.Series)
#
#         buy = False
#         exits = CustomIndicators.super_trend_return_values(close, high, low, period, multiplier, buy)
#         self.assertIsInstance(exits, pd.Series)
#
# if __name__ == '__main__':
#     unittest.main()
