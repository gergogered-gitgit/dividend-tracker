import unittest
import pandas as pd

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

    def test_normalize_yield_uses_history_rate_when_info_rate_missing(self):
        info = {}

        self.assertAlmostEqual(
            data._normalize_yield(info, price=100.0, annual_rate=6.71),
            0.0671,
            places=4,
        )


class HistoryFallbackTests(unittest.TestCase):
    def test_price_from_history_uses_last_close(self):
        class FakeStock:
            def history(self, period="5d", auto_adjust=False):
                return pd.DataFrame(
                    {"Close": [98.1, 99.4, 100.2]},
                    index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
                )

        self.assertAlmostEqual(data._price_from_history(FakeStock()), 100.2, places=4)

    def test_annual_dividend_rate_from_history_sums_recent_dividends(self):
        class FakeStock:
            @property
            def dividends(self):
                return pd.Series(
                    [1.0, 1.5, 2.25],
                    index=pd.to_datetime(["2025-06-01", "2025-12-01", "2026-04-01"]),
                )

        rate = data._annual_dividend_rate_from_history(FakeStock(), as_of=pd.Timestamp("2026-05-06"))
        self.assertAlmostEqual(rate, 4.75, places=4)


if __name__ == "__main__":
    unittest.main()
