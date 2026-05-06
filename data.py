"""
Dividend data layer using yfinance.
Fetches dividend history, upcoming payments, stock info, exchange rates,
search, dividend growth, and ex-dividend alerts.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor


YAHOO_EXCHANGE_SUFFIXES = [
    # Europe
    "AS", "L", "DE", "F", "HM", "DU", "SG", "BE", "MU", "HA", "SW", "PA",
    "BR", "LS", "MC", "MI", "VI", "ST", "CO", "HE", "OL", "IC", "IR", "WA",
    "PR", "BD", "AT", "IS", "TA",
    # North and South America
    "TO", "V", "CN", "NE", "MX", "SA", "BA", "SN",
    # Asia-Pacific
    "T", "HK", "SS", "SZ", "SI", "AX", "NZ", "KS", "KQ", "TW", "TWO",
    "NS", "BO", "JK", "KL", "BK",
    # Africa and Middle East
    "JO", "CA", "QA", "AE",
]

MARKET_DATA_VERSION = "2026-05-06-yield-v2"


# --- Stock info & search ---

@st.cache_data(ttl=3600)  # cache for 1 hour
def get_stock_info(ticker: str, market_data_version: str = MARKET_DATA_VERSION) -> dict:
    """
    Get basic stock info: name, price, dividend yield, currency, and dividend dates.
    Returns a dict with the relevant fields, or empty values on failure.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Try multiple field names — yfinance changes these across versions
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("regularMarketPreviousClose")
            or info.get("previousClose")
        )

        # Fallback: use fast_info if .info didn't have the price
        if not price:
            try:
                price = stock.fast_info.get("lastPrice") or stock.fast_info.get("regularMarketPrice")
            except Exception:
                pass

        return {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "price": price,
            "currency": info.get("currency") or info.get("financialCurrency") or "USD",
            "dividend_rate": info.get("dividendRate") or info.get("trailingAnnualDividendRate"),
            "dividend_yield": _normalize_yield(info, price),
            "ex_dividend_date": _timestamp_to_date(info.get("exDividendDate")),
            "dividend_date": _timestamp_to_date(info.get("dividendDate")),
        }
    except Exception:
        return {
            "name": ticker,
            "price": None,
            "currency": "USD",
            "dividend_rate": None,
            "dividend_yield": None,
            "ex_dividend_date": None,
            "dividend_date": None,
        }


def search_tickers(query: str) -> list[dict]:
    """
    Search Yahoo Finance for tickers matching a query string.
    Returns a list of dicts with: ticker, name, type, exchange.
    """
    if not query or len(query) < 2:
        return []

    output = []
    seen = set()
    symbols_to_expand = []

    for result in _lookup_ticker_symbols(_ticker_symbol_candidates(query)):
        if result and result["ticker"] not in seen:
            output.append(result)
            seen.add(result["ticker"])
            if _is_expandable_base_symbol(result["ticker"]):
                symbols_to_expand.append(result["ticker"])

    try:
        results = yf.Search(query)
        quotes = results.quotes if hasattr(results, "quotes") else []
        for q in quotes[:10]:
            ticker = q.get("symbol", "")
            if not ticker or ticker in seen:
                continue
            output.append({
                "ticker": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname") or q.get("symbol", ""),
                "type": q.get("quoteType", ""),
                "exchange": q.get("exchange", ""),
            })
            seen.add(ticker)

            if (
                q.get("quoteType") in {"EQUITY", "ETF"}
                and _is_expandable_base_symbol(ticker)
                and _should_expand_symbol(query, ticker)
            ):
                symbols_to_expand.append(ticker)
    except Exception:
        pass

    for symbol in _unique_preserving_order(symbols_to_expand)[:3]:
        for result in _lookup_ticker_symbols(_exchange_symbol_variants(symbol)):
            if result and result["ticker"] not in seen:
                output.append(result)
                seen.add(result["ticker"])

    return output


# --- Dividend data ---

@st.cache_data(ttl=3600)
def get_dividend_history(ticker: str, years: int = 3) -> pd.DataFrame:
    """
    Get dividend payment history for a ticker.
    Returns DataFrame with columns: date, amount.
    """
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        if dividends.empty:
            return pd.DataFrame(columns=["date", "amount"])

        # Strip timezone info to avoid comparison issues
        dividends.index = dividends.index.tz_localize(None)

        cutoff = pd.Timestamp(datetime.now() - timedelta(days=years * 365))
        dividends = dividends[dividends.index >= cutoff]

        df = dividends.reset_index()
        df.columns = ["date", "amount"]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df.sort_values("date", ascending=False)
    except Exception:
        return pd.DataFrame(columns=["date", "amount"])


def estimate_upcoming_dividends(ticker: str, shares: float) -> list[dict]:
    """
    Estimate upcoming dividend payments based on historical pattern.
    Projects up to 12 months of future payments.
    Returns a list of dicts with: expected_date, amount_per_share, total_amount, frequency.
    """
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends

        if dividends.empty:
            return []

        # Strip timezone info to avoid comparison issues
        dividends.index = dividends.index.tz_localize(None)
        now = pd.Timestamp.now()

        # Get last 2 years of dividends to find the pattern
        cutoff = now - pd.Timedelta(days=730)
        recent = dividends[dividends.index >= cutoff]

        if recent.empty:
            return []

        # Determine payment frequency
        one_year_ago = now - pd.Timedelta(days=365)
        last_year = recent[recent.index >= one_year_ago]
        payments_per_year = len(last_year)

        if payments_per_year == 0:
            last_div = recent.iloc[-1]
            return [{
                "expected_date": None,
                "amount_per_share": round(float(last_div), 4),
                "total_amount": round(float(last_div) * shares, 2),
                "frequency": "unknown",
            }]

        # Calculate average interval between payments
        if len(recent) >= 2:
            dates = recent.index.sort_values()
            intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 365

        avg_amount = float(recent.mean())
        freq = _frequency_label(payments_per_year)

        # Project upcoming payments — up to 12 months out
        upcoming = []
        next_date = recent.index.max()
        for _ in range(max(payments_per_year, 4) + 2):
            next_date = next_date + pd.Timedelta(days=int(avg_interval))
            if next_date < now:
                continue
            if next_date > now + pd.Timedelta(days=365):
                break
            upcoming.append({
                "expected_date": next_date.date(),
                "amount_per_share": round(avg_amount, 4),
                "total_amount": round(avg_amount * shares, 2),
                "frequency": freq,
            })

        return upcoming
    except Exception:
        return []


def get_annual_dividend_income(ticker: str, shares: float) -> float:
    """
    Calculate expected annual dividend income for a holding.
    Uses the trailing annual dividend rate from yfinance.
    """
    info = get_stock_info(ticker)
    rate = info.get("dividend_rate")
    if rate:
        return round(rate * shares, 2)
    return 0.0


# --- Dividend growth ---

@st.cache_data(ttl=3600)
def get_dividend_growth(ticker: str) -> dict:
    """
    Calculate year-over-year dividend growth.
    Compares total dividends paid in the last 12 months vs the prior 12 months.
    Returns: {"growth_pct": float or None, "direction": "up"/"down"/"flat"/"n/a"}
    """
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        if dividends.empty:
            return {"growth_pct": None, "direction": "n/a"}

        # Strip timezone info to avoid comparison issues
        dividends.index = dividends.index.tz_localize(None)

        now = pd.Timestamp.now()
        one_year_ago = now - pd.Timedelta(days=365)
        two_years_ago = now - pd.Timedelta(days=730)

        recent_year = dividends[(dividends.index >= one_year_ago) & (dividends.index < now)]
        prior_year = dividends[(dividends.index >= two_years_ago) & (dividends.index < one_year_ago)]

        if prior_year.empty or recent_year.empty:
            return {"growth_pct": None, "direction": "n/a"}

        recent_total = recent_year.sum()
        prior_total = prior_year.sum()

        if prior_total == 0:
            return {"growth_pct": None, "direction": "n/a"}

        growth = ((recent_total - prior_total) / prior_total) * 100

        if growth > 0.5:
            direction = "up"
        elif growth < -0.5:
            direction = "down"
        else:
            direction = "flat"

        return {"growth_pct": round(growth, 1), "direction": direction}
    except Exception:
        return {"growth_pct": None, "direction": "n/a"}


# --- Alerts ---

def get_upcoming_alerts(holdings: list[dict], days_ahead: int = 14) -> list[dict]:
    """
    Check all holdings for upcoming ex-dividend dates within the next N days.
    Returns a list of alerts sorted by days remaining (most urgent first).
    """
    alerts = []
    today = datetime.now().date()
    cutoff = today + timedelta(days=days_ahead)

    for h in holdings:
        info = get_stock_info(h["ticker"])
        ex_date = info.get("ex_dividend_date")
        if ex_date and today <= ex_date <= cutoff:
            days_left = (ex_date - today).days
            alerts.append({
                "ticker": h["ticker"],
                "company": info["name"],
                "ex_date": ex_date,
                "days_left": days_left,
                "urgent": days_left <= 3,
            })

    return sorted(alerts, key=lambda a: a["days_left"])


# --- Currency conversion ---

@st.cache_data(ttl=1800)  # cache for 30 min
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Get the current exchange rate from one currency to another.
    Returns the multiplier: amount_in_from * rate = amount_in_to.
    """
    if from_currency == to_currency:
        return 1.0

    try:
        pair = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(pair)
        rate = ticker.info.get("regularMarketPrice")
        if rate:
            return float(rate)

        # Fallback: try via USD as intermediate
        if from_currency != "USD" and to_currency != "USD":
            rate_from_usd = get_exchange_rate(from_currency, "USD")
            rate_usd_to = get_exchange_rate("USD", to_currency)
            return rate_from_usd * rate_usd_to

        return 1.0
    except Exception:
        return 1.0


def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert an amount from one currency to another."""
    if amount is None:
        return None
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)


def fmt_money(value: float, currency: str) -> str:
    """Format a monetary value with appropriate decimals. HUF has no decimals."""
    if value is None:
        return "N/A"
    if currency == "HUF":
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


# --- Helper functions ---

def _normalize_yield(info: dict, price: float = None) -> float:
    """
    Get dividend yield as a decimal where 0.02 = 2%.
    Yahoo's dividendYield field is percentage points (0.38 = 0.38%),
    while trailingAnnualDividendYield is already decimal (0.0038).
    yfinance sometimes returns values >1 (e.g. 2.0 meaning 2%) — normalize those.
    """
    raw_yield = _to_float(info.get("dividendYield"))
    trailing_yield = _to_float(info.get("trailingAnnualDividendYield"))
    implied_yield = _implied_yield_from_rate(info, price)

    candidates = []
    if raw_yield is not None:
        candidates.append(raw_yield / 100)
    if trailing_yield is not None:
        candidates.append(trailing_yield)

    if not candidates:
        return None

    if implied_yield is not None:
        return min(candidates, key=lambda candidate: abs(candidate - implied_yield))

    return candidates[0]


def _implied_yield_from_rate(info: dict, price: float = None) -> float:
    """Calculate dividend yield from annual dividend rate and price when available."""
    annual_rate = _to_float(info.get("dividendRate"))
    stock_price = _to_float(
        price
        or info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("regularMarketPreviousClose")
        or info.get("previousClose")
    )
    if not annual_rate or not stock_price:
        return None
    return annual_rate / stock_price


def _to_float(value) -> float:
    """Convert numeric API values to float, or return None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ticker_symbol_candidates(query: str) -> list[str]:
    """Build direct lookups for exact ticker searches."""
    symbol = query.strip().upper()
    if not symbol or " " in symbol:
        return []

    if "." in symbol:
        return [symbol]

    if len(symbol) > 6:
        return []

    return [symbol]


def _is_expandable_base_symbol(symbol: str) -> bool:
    """Return whether a symbol is a short unsuffixed ticker worth exchange probing."""
    return bool(symbol) and "." not in symbol and len(symbol) <= 5


def _should_expand_symbol(query: str, symbol: str) -> bool:
    """Decide whether a Yahoo result should get exchange-variant probing."""
    normalized_query = query.strip().upper()
    if not normalized_query or "." in normalized_query:
        return False
    if normalized_query == symbol:
        return True
    return len(normalized_query) > 5 or " " in normalized_query


def _unique_preserving_order(items: list[str]) -> list[str]:
    """Deduplicate a list while preserving its order."""
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _exchange_symbol_variants(symbol: str) -> list[str]:
    """Build common Yahoo exchange variants for an unsuffixed ticker symbol."""
    symbol = symbol.strip().upper()
    if not symbol or "." in symbol:
        return []

    return [f"{symbol}.{suffix}" for suffix in YAHOO_EXCHANGE_SUFFIXES]


def _lookup_ticker_symbols(symbols: list[str]) -> list[dict]:
    """Look up Yahoo symbols concurrently while preserving the input order."""
    if not symbols:
        return []

    with ThreadPoolExecutor(max_workers=12) as executor:
        return list(executor.map(_lookup_ticker_symbol, symbols))


@st.cache_data(ttl=3600)
def _lookup_ticker_symbol(symbol: str) -> dict:
    """Look up a specific Yahoo symbol and return a search result row if it exists."""
    try:
        info = yf.Ticker(symbol).info
    except Exception:
        return None

    quote_type = info.get("quoteType")
    name = info.get("longName") or info.get("shortName")
    exchange = info.get("exchange")

    if not quote_type or quote_type == "NONE" or not name:
        return None

    return {
        "ticker": symbol,
        "name": name,
        "type": quote_type,
        "exchange": exchange or "",
    }


def _timestamp_to_date(ts):
    """Convert a unix timestamp to a date, or return None."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts).date()
    except Exception:
        return None


def _frequency_label(payments_per_year: int) -> str:
    """Convert payment count to a human label."""
    if payments_per_year >= 11:
        return "monthly"
    elif payments_per_year >= 3:
        return "quarterly"
    elif payments_per_year >= 1.5:
        return "semi-annual"
    elif payments_per_year >= 0.5:
        return "annual"
    return "irregular"
