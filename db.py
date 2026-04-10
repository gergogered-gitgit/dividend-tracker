"""
Supabase database layer for portfolio holdings.
Handles all CRUD operations for the holdings table.
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_client() -> Client:
    """
    Create and return a Supabase client.
    Checks st.secrets first (for Streamlit Cloud), then falls back to .env.
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except (KeyError, FileNotFoundError):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_KEY. "
            "Set them in .env (local) or Streamlit secrets (cloud). "
            "See .env.example for details."
        )
    return create_client(url, key)


def get_holdings() -> list[dict]:
    """Fetch all holdings, sorted by ticker."""
    client = get_client()
    response = client.table("holdings").select("*").order("ticker").execute()
    return response.data


def add_holding(ticker: str, shares: float, company_name: str = None, currency: str = "USD") -> dict:
    """Add a new holding."""
    client = get_client()
    row = {
        "ticker": ticker.upper().strip(),
        "shares": shares,
        "company_name": company_name,
        "currency": currency,
    }
    response = client.table("holdings").insert(row).execute()
    return response.data[0]


def update_holding(holding_id: str, updates: dict) -> dict:
    """Update an existing holding by ID."""
    client = get_client()
    if "ticker" in updates:
        updates["ticker"] = updates["ticker"].upper().strip()
    response = (
        client.table("holdings")
        .update(updates)
        .eq("id", holding_id)
        .execute()
    )
    return response.data[0]


def delete_holding(holding_id: str) -> None:
    """Delete a holding by ID."""
    client = get_client()
    client.table("holdings").delete().eq("id", holding_id).execute()
