import unittest
from unittest.mock import patch
import pandas as pd

import data


class FakeYahooSearch:
    def __init__(self, quotes):
        self.quotes = quotes


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

    def test_get_stock_info_keeps_fallbacks_when_info_raises(self):
        class FakeStock:
            @property
            def info(self):
                raise RuntimeError("info unavailable")

            @property
            def fast_info(self):
                return {"lastPrice": 100.0}

            @property
            def dividends(self):
                return pd.Series(
                    [6.71],
                    index=pd.to_datetime(["2026-01-01"]),
                )

        with patch.object(data.yf, "Ticker", return_value=FakeStock()):
            info = data.get_stock_info("XVALO")

        self.assertEqual(info["name"], "XVALO")
        self.assertAlmostEqual(info["price"], 100.0, places=4)
        self.assertAlmostEqual(info["dividend_rate"], 6.71, places=4)
        self.assertAlmostEqual(info["dividend_yield"], 0.0671, places=4)

    def test_get_stock_info_normalizes_pence_quoted_uk_listings(self):
        class FakeStock:
            @property
            def info(self):
                return {
                    "currency": "GBp",
                    "currentPrice": 670,
                    "dividendRate": 30,
                    "longName": "Invesco FTSE All-World UCITS ETF USD Accumulation",
                }

        with patch.object(data.yf, "Ticker", return_value=FakeStock()):
            info = data.get_stock_info("FWRG.L")

        self.assertEqual(info["currency"], "GBP")
        self.assertAlmostEqual(info["price"], 6.7, places=4)
        self.assertAlmostEqual(info["dividend_rate"], 0.3, places=4)


class SearchRankingTests(unittest.TestCase):
    def test_wmt_search_prefers_german_listing_from_company_anchor(self):
        def fake_search(term):
            if term == "WMT":
                return FakeYahooSearch([
                    {"symbol": "WMT", "longname": "Walmart Inc.", "quoteType": "EQUITY", "exchange": "NYQ"},
                ])
            if term == "Walmart Inc.":
                return FakeYahooSearch([
                    {"symbol": "WMT.DE", "longname": "Walmart Inc.", "quoteType": "EQUITY", "exchange": "GER"},
                    {"symbol": "WMT", "longname": "Walmart Inc.", "quoteType": "EQUITY", "exchange": "NYQ"},
                ])
            return FakeYahooSearch([])

        with patch.object(data.yf, "Search", side_effect=fake_search), patch.object(data, "_lookup_ticker_symbols", return_value=[]):
            results = data.search_tickers("WMT")

        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0]["ticker"], "WMT.DE")

    def test_vale_search_prefers_local_listing_from_company_anchor(self):
        def fake_search(term):
            if term == "Vale":
                return FakeYahooSearch([
                    {"symbol": "VALE", "longname": "Vale S.A.", "quoteType": "EQUITY", "exchange": "NYQ"},
                ])
            if term == "Vale S.A.":
                return FakeYahooSearch([
                    {"symbol": "CVLB.F", "longname": "Vale S.A.", "quoteType": "EQUITY", "exchange": "FRA"},
                    {"symbol": "VALE", "longname": "Vale S.A.", "quoteType": "EQUITY", "exchange": "NYQ"},
                ])
            return FakeYahooSearch([])

        with patch.object(data.yf, "Search", side_effect=fake_search), patch.object(data, "_lookup_ticker_symbols", return_value=[]):
            results = data.search_tickers("Vale")

        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0]["ticker"], "CVLB.F")


class DisplayNameTests(unittest.TestCase):
    def test_clean_display_name_strips_ticker_suffix(self):
        self.assertEqual(data._clean_display_name("Vale S.A. (VALE)", "VALE"), "Vale S.A.")
        self.assertEqual(data._clean_display_name("Walmart Inc. - WMT", "WMT"), "Walmart Inc.")

    def test_resolve_company_name_uses_aliases(self):
        self.assertEqual(data.resolve_company_name("ABEA.DE", yahoo_name="ABEA.DE"), "Alphabet Inc.")
        self.assertEqual(data.resolve_company_name("AMZN", yahoo_name="AMZN"), "Amazon.com, Inc.")
        self.assertEqual(data.resolve_company_name("APC.DE", yahoo_name="APC.DE"), "Apple Inc.")


class AlertFallbackTests(unittest.TestCase):
    def test_get_upcoming_alerts_uses_confirmed_ex_dividend_date(self):
        holdings = [{"ticker": "WMT", "shares": 10, "company_name": "Walmart Inc."}]
        fake_info = {
            "name": "WMT",
            "ex_dividend_date": pd.Timestamp("2026-05-10").date(),
        }

        with patch.object(data, "get_stock_info", return_value=fake_info), patch.object(data, "estimate_upcoming_dividends", return_value=[]):
            alerts = data.get_upcoming_alerts(holdings, days_ahead=14)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["source"], "confirmed")
        self.assertEqual(alerts[0]["ex_date"], pd.Timestamp("2026-05-10").date())
        self.assertEqual(alerts[0]["company"], "Walmart Inc.")

    def test_get_upcoming_alerts_falls_back_to_estimated_dividend(self):
        holdings = [{"ticker": "XVALO.MC", "shares": 10, "company_name": "Vale S.A."}]
        fake_info = {
            "name": "XVALO.MC",
            "ex_dividend_date": None,
        }
        projected_date = (pd.Timestamp.now().normalize() + pd.Timedelta(days=7)).date()
        projected = [{
            "expected_date": projected_date,
            "amount_per_share": 1.0,
            "total_amount": 10.0,
            "frequency": "quarterly",
        }]

        with patch.object(data, "get_stock_info", return_value=fake_info), patch.object(data, "estimate_upcoming_dividends", return_value=projected):
            alerts = data.get_upcoming_alerts(holdings, days_ahead=14)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["source"], "estimated")
        self.assertEqual(alerts[0]["ex_date"], projected_date)
        self.assertEqual(alerts[0]["company"], "Vale S.A.")


if __name__ == "__main__":
    unittest.main()
