# Dividend Tracker

Track your dividend portfolio in one place. See upcoming payments on a visual calendar, monitor dividend growth trends, estimate tax withholding, and switch between EUR, USD, and HUF. Powered by live Yahoo Finance data.

## Features

- **Portfolio management** - search and add stocks/ETFs from Yahoo Finance, edit shares inline, including fractional shares up to 7 decimal places
- **Dividend calendar** - visual monthly calendar showing estimated upcoming dividend payments
- **Ex-dividend alerts** - warns you when ex-dividend dates are approaching
- **Dividend date tracking** - shows both ex-dividend dates and next payment dates when Yahoo Finance provides them
- **Dividend growth tracking** - year-over-year dividend growth per holding
- **Dividend yield display** - normalizes Yahoo Finance yield fields so values such as `0.38` display as `0.38%`, not `38%`
- **Tax withholding estimates** - configurable rates for different countries/treaties
- **Multi-currency** - live conversion between EUR, USD, and HUF
- **3 themes** - Modern, Default, and Retro

## Dividend Dates

The app keeps two dividend date concepts separate:

- **Ex-dividend date** - the eligibility cutoff. You generally need to own the stock before this date to receive the next dividend.
- **Pay date** - the date the dividend cash is expected to be paid. This is the date most useful for income planning.

The portfolio table shows both dates when Yahoo Finance provides them. The dividend calendar estimates upcoming payment dates from recent dividend history, so those calendar dates are projections rather than guaranteed company announcements.

## Setup

### 1. Supabase (database)

- Create a free project at [supabase.com](https://supabase.com)
- Go to **SQL Editor**, paste and run the contents of `supabase_schema.sql`
- Copy your **Project URL** and **Publishable Key** from Project Settings

### 2. Local development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your Supabase credentials

# Run the app
streamlit run app.py
```

### 3. Deploy to Streamlit Cloud

- Push this repo to GitHub
- Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
- Add your Supabase credentials in **Settings > Secrets**:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-publishable-key"
```

## Tech Stack

- **Streamlit** - web interface
- **yfinance** - live stock/dividend data from Yahoo Finance
- **Supabase** - portfolio storage (free tier)
- **Python** - pandas for data wrangling
