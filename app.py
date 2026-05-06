"""
Dividend Tracker — Streamlit app.
Track your portfolio dividends with a simple interface.
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import calendar as cal_module

import db
import data
from themes import get_theme_css

# --- Page config ---
st.set_page_config(
    page_title="Dividend Tracker",
    page_icon="$",
    layout="wide",
)

# --- Sidebar ---
st.sidebar.title("Dividend Tracker")

display_cur = st.sidebar.selectbox("Display currency", ["EUR", "USD", "HUF"], index=0)
st.sidebar.divider()
page = st.sidebar.radio("Navigate", ["Portfolio", "Dividend Calendar", "Summary"])

if st.sidebar.button("Refresh market data"):
    st.cache_data.clear()
    st.rerun()

# Theme at the bottom of sidebar
st.sidebar.divider()
theme = st.sidebar.selectbox("Theme", ["Modern", "Default", "Retro"], index=0)

# Inject theme CSS
st.markdown(get_theme_css(theme), unsafe_allow_html=True)


# --- Helper to load holdings (with error handling) ---
def load_holdings():
    try:
        return db.get_holdings()
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        st.info("Make sure your .env file has SUPABASE_URL and SUPABASE_KEY set correctly.")
        st.stop()


# ============================================================
# PORTFOLIO PAGE
# ============================================================
if page == "Portfolio":

    holdings = load_holdings()

    # --- Alerts ---
    if holdings:
        alerts = data.get_upcoming_alerts(holdings)
        if alerts:
            alert_label = f"Upcoming ex-dividend dates - next 14 days ({len(alerts)})"
            with st.expander(alert_label, expanded=False):
                for a in alerts:
                    days_text = "TODAY" if a["days_left"] == 0 else f"in {a['days_left']} day{'s' if a['days_left'] != 1 else ''}"
                    holding_label = a.get("company") or a["ticker"]
                    st.markdown(
                        f'<div class="alert-item">'
                        f'<span class="alert-text"><strong>{holding_label}</strong> ({a["ticker"]}) ex-dividend date ({a["ex_date"]})</span>'
                        f'<span class="alert-days">{days_text}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # --- Add new holding ---
    st.subheader("Add New Holding")
    search_query = st.text_input("Search company or ETF", placeholder="Type to search... e.g. Apple, Vanguard, TSLA")

    if search_query:
        results = data.search_tickers(search_query)
        if results:
            options = {f"{r['ticker']} — {r['name']} ({r['type']}, {r['exchange']})": r for r in results}
            selected_label = st.selectbox("Select from results", list(options.keys()))
            selected = options[selected_label]

            # Show preview
            info = data.get_stock_info(selected["ticker"])
            price_display = data.convert_amount(info["price"], info.get("currency", "USD"), display_cur)
            col1, col2, col3 = st.columns(3)
            col1.metric("Ticker", selected["ticker"])
            col2.metric(f"Price ({display_cur})", data.fmt_money(price_display, display_cur) if price_display else "N/A")
            col3.metric("Yield", f"{info['dividend_yield']:.2%}" if info["dividend_yield"] else "No dividend")

            shares = st.number_input(
                "Number of shares",
                min_value=0.0000001,
                value=1.0,
                step=0.0000001,
                format="%.7f",
            )

            if st.button("Add holding"):
                db.add_holding(
                    ticker=selected["ticker"],
                    shares=shares,
                    company_name=info["name"],
                    currency=info.get("currency", "USD"),
                )
                st.success(f"Added {selected['ticker']} ({info['name']})")
                st.cache_data.clear()
                st.rerun()
        else:
            st.caption("No results found.")

    # --- Holdings table ---
    if not holdings:
        st.info("No holdings yet. Add your first one above.")
        st.stop()

    st.caption(f"All values shown in {display_cur}")

    # Build table data
    rows = []
    for h in holdings:
        info = data.get_stock_info(h["ticker"])
        stock_cur = info.get("currency") or h.get("currency") or "USD"
        annual_div = data.get_annual_dividend_income(h["ticker"], float(h["shares"]))
        growth = data.get_dividend_growth(h["ticker"])

        # Format growth
        if growth["direction"] == "up":
            growth_str = f"+{growth['growth_pct']}% YoY"
            growth_class = "growth-up"
        elif growth["direction"] == "down":
            growth_str = f"{growth['growth_pct']}% YoY"
            growth_class = "growth-down"
        elif growth["direction"] == "flat":
            growth_str = "Flat"
            growth_class = "growth-flat"
        else:
            growth_str = "N/A"
            growth_class = "growth-na"

        rows.append({
            "id": h["id"],
            "Ticker": h["ticker"],
            "Company": info["name"],
            "Shares": float(h["shares"]),
            "Price": data.convert_amount(info["price"], stock_cur, display_cur),
            "Yield": f"{info['dividend_yield']:.2%}" if info["dividend_yield"] else "N/A",
            "Annual Div": data.convert_amount(annual_div, stock_cur, display_cur),
            "Div Growth": growth_str,
            "_growth_class": growth_class,
            "Pay Date": str(info.get("dividend_date")) if info.get("dividend_date") else "N/A",
            "Ex-Div Date": str(info["ex_dividend_date"]) if info["ex_dividend_date"] else "—",
            "_stock_cur": stock_cur,
        })

    # Display as a dataframe
    df = pd.DataFrame(rows)
    display_df = df[
        ["Ticker", "Company", "Shares", "Price", "Yield", "Annual Div", "Div Growth", "Ex-Div Date", "Pay Date"]
    ].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(f"Price ({display_cur})", format="%.2f"),
            "Annual Div": st.column_config.NumberColumn(f"Annual Div ({display_cur})", format="%.2f"),
            "Shares": st.column_config.NumberColumn("Shares", format="%.7f"),
        },
    )

    # --- Manage holdings ---
    st.subheader("Manage holdings")
    for h in holdings:
        with st.expander(f"{h['ticker']} — {h.get('company_name', '')}"):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                new_shares = st.number_input(
                    "Shares",
                    min_value=0.0000001,
                    value=float(h["shares"]),
                    step=0.0000001,
                    format="%.7f",
                    key=f"shares_{h['id']}",
                )
            with col2:
                if st.button("Update", key=f"update_{h['id']}"):
                    db.update_holding(h["id"], {"shares": new_shares})
                    st.success(f"Updated {h['ticker']}")
                    st.cache_data.clear()
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_{h['id']}", type="secondary"):
                    db.delete_holding(h["id"])
                    st.success(f"Deleted {h['ticker']}")
                    st.cache_data.clear()
                    st.rerun()


# ============================================================
# DIVIDEND CALENDAR PAGE
# ============================================================
elif page == "Dividend Calendar":

    holdings = load_holdings()
    if not holdings:
        st.info("Add holdings first to see upcoming dividends.")
        st.stop()

    # --- Calendar month navigation ---
    today = date.today()
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = today.year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = today.month

    col_prev, col_label, col_next, col_today = st.columns([1, 4, 1, 1])
    with col_prev:
        if st.button("<"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month < 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            st.rerun()
    with col_label:
        month_name = cal_module.month_name[st.session_state.cal_month]
        st.markdown(f"### {month_name} {st.session_state.cal_year}")
    with col_next:
        if st.button(">"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month > 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            st.rerun()
    with col_today:
        if st.button("Today"):
            st.session_state.cal_year = today.year
            st.session_state.cal_month = today.month
            st.rerun()

    # --- Collect all upcoming dividends ---
    all_upcoming = []
    for h in holdings:
        info = data.get_stock_info(h["ticker"])
        stock_cur = info.get("currency") or h.get("currency") or "USD"
        upcoming = data.estimate_upcoming_dividends(h["ticker"], float(h["shares"]))
        for div in upcoming:
            if div["expected_date"]:
                all_upcoming.append({
                    "date": div["expected_date"],
                    "ticker": h["ticker"],
                    "company": info["name"],
                    "per_share": div["amount_per_share"],
                    "total_eur": data.convert_amount(div["total_amount"], stock_cur, display_cur),
                    "frequency": div["frequency"],
                    "stock_cur": stock_cur,
                })

    # --- Build calendar grid HTML ---
    year = st.session_state.cal_year
    month = st.session_state.cal_month

    # Events for this month
    month_events = [e for e in all_upcoming if e["date"].year == year and e["date"].month == month]
    events_by_day = {}
    for e in month_events:
        d = e["date"].day
        events_by_day.setdefault(d, []).append(e)

    month_total = sum(e["total_eur"] or 0 for e in month_events)

    # Calendar math
    first_weekday, days_in_month = cal_module.monthrange(year, month)
    # Monday = 0 in calendar module, which matches our grid

    html = '<div class="cal-grid">'
    for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        html += f'<div class="cal-header">{day_name}</div>'

    # Empty cells before first day
    for _ in range(first_weekday):
        html += '<div class="cal-day empty"></div>'

    # Day cells
    for day in range(1, days_in_month + 1):
        events = events_by_day.get(day, [])
        is_today = (year == today.year and month == today.month and day == today.day)
        classes = "cal-day"
        if events:
            classes += " has-div"
        if is_today:
            classes += " today"

        html += f'<div class="{classes}"><div class="cal-day-num">{day}</div>'
        for e in events:
            amt = data.fmt_money(e["total_eur"], display_cur) if e["total_eur"] else "?"
            html += (
                f'<div class="cal-chip">'
                f'<span class="cal-chip-ticker">{e["ticker"]}</span>'
                f'<span class="cal-chip-amount">{amt}</span>'
                f'</div>'
            )
        html += '</div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Month total
    total_display = data.fmt_money(month_total, display_cur)
    total_label = f"Total dividends in {month_name}" if month_total > 0 else f"No dividends expected in {month_name}"
    st.markdown(
        f'<div class="cal-month-total">'
        f'<span class="cal-total-label">{total_label}</span>'
        f'<span class="cal-total-value">{total_display} {display_cur}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Upcoming payments table ---
    st.subheader("Upcoming Payments")
    if all_upcoming:
        cal_df = pd.DataFrame(all_upcoming).sort_values("date")
        cal_df = cal_df.rename(columns={
            "date": "Date",
            "ticker": "Ticker",
            "company": "Company",
            "per_share": "Per Share",
            "total_eur": f"Payout ({display_cur})",
            "frequency": "Frequency",
        })
        st.dataframe(
            cal_df[["Date", "Ticker", "Company", "Per Share", f"Payout ({display_cur})", "Frequency"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Per Share": st.column_config.NumberColumn("Per Share", format="%.4f"),
                f"Payout ({display_cur})": st.column_config.NumberColumn(f"Payout ({display_cur})", format="%.2f"),
            },
        )
    else:
        st.info("No upcoming dividends found.")

    # --- 12-month bar chart ---
    st.subheader(f"Monthly Breakdown — Expected Payouts ({display_cur})")
    monthly_data = {}
    for e in all_upcoming:
        month_key = e["date"].strftime("%Y-%m")
        monthly_data[month_key] = monthly_data.get(month_key, 0) + (e["total_eur"] or 0)

    # Build 12 months starting from current month
    chart_months = []
    for i in range(12):
        m = today.month + i
        y = today.year
        while m > 12:
            m -= 12
            y += 1
        key = f"{y}-{m:02d}"
        label = cal_module.month_abbr[m]
        chart_months.append({"Month": label, f"Payout ({display_cur})": monthly_data.get(key, 0)})

    chart_df = pd.DataFrame(chart_months)
    st.bar_chart(chart_df.set_index("Month"))


# ============================================================
# SUMMARY PAGE
# ============================================================
elif page == "Summary":

    holdings = load_holdings()
    if not holdings:
        st.info("Add holdings first to see your summary.")
        st.stop()

    # --- Calculate totals ---
    total_value = 0.0
    total_annual_div = 0.0
    breakdown = []

    for h in holdings:
        info = data.get_stock_info(h["ticker"])
        stock_cur = info.get("currency") or h.get("currency") or "USD"
        shares = float(h["shares"])

        # Portfolio value
        value = 0.0
        if info["price"]:
            value = data.convert_amount(info["price"] * shares, stock_cur, display_cur) or 0
            total_value += value

        # Annual dividend
        annual = data.get_annual_dividend_income(h["ticker"], shares)
        annual_display = data.convert_amount(annual, stock_cur, display_cur) or 0
        total_annual_div += annual_display

        breakdown.append({
            "Name": info["name"],
            "Ticker": h["ticker"],
            f"Value ({display_cur})": value,
            f"Annual Div ({display_cur})": annual_display,
        })

    # --- Metric cards ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Portfolio Value ({display_cur})", data.fmt_money(total_value, display_cur))
    col2.metric(f"Annual Dividends ({display_cur})", data.fmt_money(total_annual_div, display_cur))
    col3.metric(f"Monthly Average ({display_cur})", data.fmt_money(total_annual_div / 12, display_cur))
    portfolio_yield = (total_annual_div / total_value * 100) if total_value > 0 else 0
    col4.metric("Portfolio Yield", f"{portfolio_yield:.2f}%")

    # --- Income allocation ---
    breakdown_df = pd.DataFrame(breakdown)
    if not breakdown_df.empty:
        # Add % of income
        div_col = f"Annual Div ({display_cur})"
        value_col = f"Value ({display_cur})"
        breakdown_df["% of Income"] = (
            breakdown_df[div_col] / total_annual_div * 100
        ).round(1) if total_annual_div > 0 else 0
        breakdown_df["Holding Yield"] = (
            breakdown_df[div_col] / breakdown_df[value_col] * 100
        ).where(breakdown_df[value_col] > 0, 0).round(2)
        breakdown_df["Income Share"] = breakdown_df["% of Income"] / 100
        breakdown_df = breakdown_df.sort_values(div_col, ascending=False)

        st.subheader("Dividend Income Mix")
        chart_col, table_col = st.columns([1, 1.4])

        with chart_col:
            income_chart_df = breakdown_df[breakdown_df[div_col] > 0].copy()
            if not income_chart_df.empty:
                income_chart = (
                    alt.Chart(income_chart_df)
                    .mark_arc(innerRadius=70, outerRadius=125, stroke="#0f1116", strokeWidth=2)
                    .encode(
                        theta=alt.Theta(f"{div_col}:Q"),
                        color=alt.Color(
                            "Name:N",
                            legend=alt.Legend(title="Holding", orient="bottom", columns=1),
                            scale=alt.Scale(scheme="tableau20"),
                        ),
                        tooltip=[
                            alt.Tooltip("Name:N", title="Holding"),
                            alt.Tooltip("Ticker:N"),
                            alt.Tooltip(f"{div_col}:Q", title=f"Annual Div ({display_cur})", format=",.2f"),
                            alt.Tooltip("Income Share:Q", title="% of Income", format=".1%"),
                            alt.Tooltip(f"{value_col}:Q", title=f"Value ({display_cur})", format=",.2f"),
                            alt.Tooltip("Holding Yield:Q", title="Yield on Value", format=".2f"),
                        ],
                    )
                    .properties(height=380)
                )
                st.altair_chart(income_chart, use_container_width=True)
            else:
                st.info("No dividend income to chart yet.")

        with table_col:
            st.dataframe(
                breakdown_df[["Name", "Ticker", div_col, "% of Income", value_col, "Holding Yield"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Name": st.column_config.TextColumn("Holding"),
                    div_col: st.column_config.NumberColumn(format="%.2f"),
                    "% of Income": st.column_config.ProgressColumn(
                        "% of Income", min_value=0, max_value=100, format="%.1f%%"
                    ),
                    value_col: st.column_config.NumberColumn(format="%.2f"),
                    "Holding Yield": st.column_config.NumberColumn("Yield on Value", format="%.2f%%"),
                },
            )

    # --- Tax withholding estimate ---
    st.subheader("Tax Withholding Estimate")

    tax_rate = st.selectbox(
        "Withholding tax rate",
        options=[0, 15, 25, 27, 30, 35],
        index=1,
        format_func=lambda x: {
            0: "0% (domestic / tax-free)",
            15: "15% (US-Finland treaty)",
            25: "25% (Germany)",
            27: "27% (Denmark)",
            30: "30% (US default, no treaty)",
            35: "35% (Switzerland)",
        }.get(x, f"{x}%"),
    )

    gross = total_annual_div
    withheld = gross * (tax_rate / 100)
    net = gross - withheld

    st.markdown(
        f'<div style="border-radius:8px; overflow:hidden;">'
        f'<div class="tax-row"><span class="tax-label">Gross annual dividends</span>'
        f'<span class="tax-value">{data.fmt_money(gross, display_cur)} {display_cur}</span></div>'
        f'<div class="tax-row"><span class="tax-label">Estimated withholding ({tax_rate}%)</span>'
        f'<span class="tax-value" style="opacity:0.6;">-{data.fmt_money(withheld, display_cur)} {display_cur}</span></div>'
        f'<div class="tax-row tax-net"><span class="tax-label">Net after withholding</span>'
        f'<span class="tax-value">{data.fmt_money(net, display_cur)} {display_cur}</span></div>'
        f'</div>'
        f'<p class="tax-note">Estimate only. Actual tax depends on your residency, treaty status, and account type. '
        f'ETFs may have different withholding rules.</p>',
        unsafe_allow_html=True,
    )
