import unittest

import data


class YieldNormalizationTests(unittest.TestCase):
    def test_yfinance_percent_point_dividend_yield_uses_implied_rate(self):
        info = {
            "dividendYield": 0.38,
            "dividendRate": 1.08,
            "currentPrice": 284.18,
        }

        self.assertAlmostEqual(data._normalize_yield(info), 0.0038, places=4)

    def test_yfinance_percent_point_dividend_yield_without_price_is_normalized(self):
        info = {
            "dividendYield": 0.38,
        }

        self.assertAlmostEqual(data._normalize_yield(info), 0.0038, places=4)

    def test_decimal_trailing_yield_stays_decimal(self):
        info = {
            "trailingAnnualDividendYield": 0.0038,
        }

        self.assertAlmostEqual(data._normalize_yield(info), 0.0038, places=4)

    def test_conflicting_trailing_yield_uses_current_dividend_rate(self):
        info = {
            "dividendYield": 0.89,
            "trailingAnnualDividendYield": 0.042329624,
            "dividendRate": 3.51,
            "currentPrice": 394.41,
        }

        self.assertAlmostEqual(data._normalize_yield(info), 0.0089, places=4)

    def test_percent_yield_over_one_is_normalized(self):
        info = {
            "dividendYield": 2.5,
        }

        self.assertAlmostEqual(data._normalize_yield(info), 0.025, places=4)


if __name__ == "__main__":
    unittest.main()
