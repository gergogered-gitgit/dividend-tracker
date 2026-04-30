# Dividend Tracker

Track your dividend portfolio in one place. See upcoming payments on a visual calendar, monitor dividend growth trends, estimate tax withholding, and switch between EUR, USD, and HUF. Powered by live Yahoo Finance data.

## Features

- **Portfolio management** - search and add stocks/ETFs from Yahoo Finance, edit shares inline
- **Dividend calendar** - visual monthly calendar showing when dividends are paid
- **Ex-dividend alerts** - warns you when ex-dividend dates are approaching
- **Dividend growth tracking** - year-over-year dividend growth per holding
- **Tax withholding estimates** - configurable rates for different countries/treaties
- **Multi-currency** - live conversion between EUR, USD, and HUF
- **3 themes** - Modern, Default, and Retro

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
