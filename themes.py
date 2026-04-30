"""
Theme CSS for the Dividend Tracker Streamlit app.
Injected via st.markdown(unsafe_allow_html=True).
"""


def get_theme_css(theme: str) -> str:
    """Return the full CSS block for the selected theme."""
    base = _base_css()
    if theme == "Retro":
        return base + _retro_css()
    elif theme == "Modern":
        return base + _modern_css()
    return base + _default_css()


def _base_css() -> str:
    """Shared structural CSS across all themes."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

    /* Alert banner */
    .alert-item {
        display: flex; align-items: center; gap: 12px; padding: 10px 16px;
        margin-bottom: 6px; border-radius: 6px; font-size: 14px; border-left: 3px solid;
    }
    .alert-text { flex: 1; }
    .alert-days { font-weight: 700; white-space: nowrap; }

    /* Dividend growth */
    .growth-up { color: #21c354; font-weight: 600; }
    .growth-down { color: #ff4b4b; font-weight: 600; }
    .growth-flat { opacity: 0.5; }
    .growth-na { opacity: 0.3; }

    /* Calendar grid */
    .cal-grid {
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-bottom: 16px;
    }
    .cal-header {
        text-align: center; padding: 8px 0; font-size: 12px; font-weight: 600;
        opacity: 0.5; text-transform: uppercase; letter-spacing: 1px;
    }
    .cal-day {
        min-height: 80px; padding: 6px 8px; border-radius: 4px;
        border: 1px solid transparent;
    }
    .cal-day-num { font-size: 13px; opacity: 0.5; margin-bottom: 4px; }
    .cal-day.today .cal-day-num { font-weight: 700; opacity: 1; }
    .cal-day.empty { opacity: 0; min-height: 0; padding: 0; }
    .cal-chip {
        display: block; padding: 3px 6px; margin-bottom: 3px; border-radius: 3px;
        font-size: 11px; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .cal-chip-ticker { font-weight: 700; }
    .cal-chip-amount { float: right; margin-left: 6px; }

    /* Month total */
    .cal-month-total {
        padding: 12px 16px; margin-bottom: 20px; border-radius: 6px;
        display: flex; justify-content: space-between; font-size: 14px;
    }
    .cal-total-label { opacity: 0.6; }
    .cal-total-value { font-weight: 700; }

    /* Tax summary */
    .tax-row {
        display: flex; justify-content: space-between; padding: 10px 16px;
        font-size: 14px;
    }
    .tax-label { opacity: 0.6; }
    .tax-value { font-weight: 600; }
    .tax-net .tax-label { opacity: 1; font-weight: 600; }
    .tax-note { font-size: 12px; opacity: 0.4; margin-top: 8px; }

    /* Frequency badges */
    .freq-badge {
        display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 600;
    }

    /* Hide Streamlit defaults we don't need */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """


def _default_css() -> str:
    return """
    <style>
    .alert-item { background: #262730; border-left-color: #ff4b4b; }
    .alert-item.urgent { background: rgba(255, 75, 75, 0.08); }
    .alert-days { color: #ff4b4b; }

    .cal-day { background: #262730; border-color: #333; }
    .cal-day.has-div { border-color: rgba(255, 75, 75, 0.25); }
    .cal-day.today { border-color: #ff4b4b; box-shadow: inset 0 0 0 1px #ff4b4b; }
    .cal-chip { background: rgba(255, 75, 75, 0.13); }
    .cal-month-total { background: #262730; border: 1px solid #333; }
    .cal-total-value { color: #21c354; }

    .tax-row { border-bottom: 1px solid #1e1e2a; }
    .tax-net .tax-value { color: #21c354; }

    .freq-badge.monthly { background: rgba(75, 123, 255, 0.13); color: #4b7bff; }
    .freq-badge.quarterly { background: rgba(33, 195, 84, 0.13); color: #21c354; }
    .freq-badge.semi-annual { background: rgba(255, 159, 67, 0.13); color: #ff9f43; }
    .freq-badge.annual { background: rgba(168, 85, 247, 0.13); color: #a855f7; }
    .freq-badge.irregular { background: rgba(255,255,255,0.05); color: #888; }
    </style>
    """


def _modern_css() -> str:
    return """
    <style>
    /* Override Streamlit's background */
    .stApp { background-color: #000000; }
    section[data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #1a1a1a; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label { color: #6b6b6b !important; font-weight: 500; }

    .alert-item { background: #0a0a0a; border-left-color: #e31937; }
    .alert-item.urgent { background: rgba(227, 25, 55, 0.06); }
    .alert-days { color: #e31937; }

    .growth-up { color: #18b818; }
    .growth-down { color: #e31937; }

    .cal-day { background: #0a0a0a; border-color: #1a1a1a; }
    .cal-day.has-div { border-color: rgba(227, 25, 55, 0.2); }
    .cal-day.today { border-color: #e31937; }
    .cal-day.today .cal-day-num { color: #e31937; }
    .cal-chip { background: rgba(227, 25, 55, 0.1); color: #d4d4d4; }
    .cal-chip-amount { color: #ffffff; }
    .cal-month-total { background: #0a0a0a; border: 1px solid #1a1a1a; }
    .cal-total-value { color: #18b818; }

    .tax-row { border-bottom: 1px solid #111; }
    .tax-net .tax-value { color: #18b818; }

    .freq-badge.monthly { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
    .freq-badge.quarterly { background: rgba(24, 184, 24, 0.1); color: #18b818; }
    .freq-badge.semi-annual { background: rgba(255, 159, 67, 0.1); color: #ff9f43; }
    .freq-badge.annual { background: rgba(227, 25, 55, 0.1); color: #e31937; }
    .freq-badge.irregular { background: rgba(255,255,255,0.03); color: #666; }
    </style>
    """


def _retro_css() -> str:
    return """
    <style>
    /* Override Streamlit's background */
    .stApp {
        background-color: #0a0a1a;
        background-image:
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a0a2e 0%, #0d0d2b 100%);
        border-right: 2px solid #ff2d95;
        box-shadow: 2px 0 20px rgba(255, 45, 149, 0.3);
    }

    .alert-item { background: rgba(13, 13, 43, 0.8); border-left-color: #ffe14d; }
    .alert-item.urgent { background: rgba(255, 225, 77, 0.05); border-left-color: #ff2d95; }
    .alert-days { color: #ffe14d; text-shadow: 0 0 5px rgba(255, 225, 77, 0.3); }
    .alert-item.urgent .alert-days { color: #ff2d95; }

    .growth-up { color: #39ff14; text-shadow: 0 0 5px rgba(57, 255, 20, 0.3); }
    .growth-down { color: #ff2d95; text-shadow: 0 0 5px rgba(255, 45, 149, 0.3); }

    .cal-day { background: rgba(13, 13, 43, 0.6); border-color: #333366; }
    .cal-day.has-div { border-color: rgba(255, 45, 149, 0.35); }
    .cal-day.today { border-color: #00f0ff; box-shadow: 0 0 10px rgba(0, 240, 255, 0.3); }
    .cal-day.today .cal-day-num { color: #00f0ff; text-shadow: 0 0 5px rgba(0, 240, 255, 0.5); }
    .cal-chip { background: rgba(255, 45, 149, 0.13); color: #e0e0ff; }
    .cal-chip-amount { color: #ffe14d; }
    .cal-month-total { background: rgba(13, 13, 43, 0.8); border: 1px solid rgba(176, 66, 255, 0.25); }
    .cal-total-value { color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.4); }

    .tax-row { border-bottom: 1px solid #1a1a3e; }
    .tax-net .tax-value { color: #39ff14; text-shadow: 0 0 8px rgba(57, 255, 20, 0.3); }

    .freq-badge { border: 1px solid; background: none !important; }
    .freq-badge.monthly { border-color: #00f0ff; color: #00f0ff; }
    .freq-badge.quarterly { border-color: #39ff14; color: #39ff14; }
    .freq-badge.semi-annual { border-color: #ffe14d; color: #ffe14d; }
    .freq-badge.annual { border-color: #b042ff; color: #b042ff; }
    .freq-badge.irregular { border-color: #555; color: #888; }
    </style>
    """
