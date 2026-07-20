import math
import sqlite3
from datetime import date, datetime
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(page_title="Stock_EPS_Fair_Value_Tool", page_icon="📈", layout="wide")

# Keep the app at the top after an initial load or Streamlit rerun.
components.html(
    """<script>
    const scrollTop = () => {
        try {
            window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'});
            const main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTo({top: 0, left: 0, behavior: 'instant'});
        } catch (e) {}
    };
    scrollTop();
    setTimeout(scrollTop, 50);
    setTimeout(scrollTop, 250);
    </script>""",
    height=0,
)

st.markdown("""
<style>
:root { --ink:#0a1630; --blue:#2563eb; --cyan:#22d3ee; --panel:#101d3d; }
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100%;}
div[data-testid="stHorizontalBlock"] > div {min-width: 0;}
div.stButton > button {
    min-height: 3.15rem; font-size: 1rem; font-weight: 750; border-radius: 10px;
}
/* Compact metric cards across valuation and account summaries. */
[data-testid="stMetric"] {
    padding: .35rem .45rem;
    min-height: 0;
}
[data-testid="stMetricLabel"] {
    font-size: .68rem;
    line-height: 1.05;
    margin-bottom: .05rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.05rem;
    line-height: 1.08;
    white-space: nowrap;
}
[data-testid="stMetricDelta"] {
    font-size: .65rem;
    line-height: 1;
}
[data-testid="stSidebar"] {min-width: 285px; max-width: 285px;}
.nav-label {font-size: .82rem; color: #777; margin-bottom: .15rem;}
.brandbar {display:flex;align-items:center;justify-content:space-between;padding:.35rem .2rem .8rem;}
.brandname {font-weight:850;font-size:1.15rem;letter-spacing:-.02em;}
.brandtag {font-size:.78rem;opacity:.7;}
.hero {
  position:relative; overflow:hidden; min-height:340px; border-radius:24px; padding:42px 50px 24px;
  background:linear-gradient(135deg,#071226 0%,#102451 52%,#0a3a5e 100%);
  color:white; box-shadow:0 24px 70px rgba(4,18,48,.22); margin:8px 0 12px;
}
.hero:before {content:"";position:absolute;width:480px;height:480px;border-radius:50%;right:-120px;top:-190px;background:radial-gradient(circle,rgba(34,211,238,.35),rgba(37,99,235,0));}
.hero:after {content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to right,transparent 0%,black 55%);}
.hero-copy {position:relative;z-index:2;max-width:720px;padding-top:8px;padding-right:250px;}
.eyebrow {display:inline-block;padding:7px 12px;border:1px solid rgba(255,255,255,.22);border-radius:999px;background:rgba(255,255,255,.08);font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}
.hero h1 {font-size:4rem;line-height:1.02;letter-spacing:-.055em;margin:22px 0 18px;max-width:740px;}
.hero p {font-size:1.15rem;line-height:1.65;color:rgba(255,255,255,.78);max-width:600px;}
.market-card {position:absolute;z-index:3;right:24px;top:24px;width:360px;padding:24px;border:1px solid rgba(255,255,255,.16);border-radius:20px;background:rgba(7,18,38,.68);backdrop-filter:blur(15px);box-shadow:0 24px 70px rgba(0,0,0,.3);}
.market-card .ticker {display:flex;justify-content:space-between;align-items:end;margin-bottom:12px;}
.market-card .price {font-size:1.9rem;font-weight:850;}
.market-card .gain {color:#5ee8a5;font-weight:750;}
.spark {width:100%;height:150px;}
.statrow {display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:8px;}
.stat {padding:7px;border-radius:10px;background:rgba(255,255,255,.06);font-size:.72rem;color:rgba(255,255,255,.6);}
.stat b {display:block;color:white;font-size:.9rem;margin-top:3px;}
.section-title {font-size:2rem;font-weight:850;letter-spacing:-.035em;margin:22px 0 6px;}
.section-copy {opacity:.72;margin-bottom:24px;}
.feature-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:8px 0 34px;}
.feature-card {border:1px solid rgba(128,128,128,.22);border-radius:18px;padding:24px;min-height:190px;background:rgba(128,128,128,.045);}
.feature-icon {font-size:1.55rem;width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:rgba(37,99,235,.12);margin-bottom:18px;}
.feature-card h3 {margin:0 0 8px;font-size:1.08rem;}
.feature-card p {margin:0;opacity:.68;line-height:1.55;font-size:.93rem;}
.proofbar {display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:22px;border-radius:18px;background:rgba(37,99,235,.07);margin:12px 0 30px;}
.proof {text-align:center;font-size:.78rem;opacity:.72;}.proof b {display:block;font-size:1.35rem;opacity:1;margin-bottom:4px;}
.site-footer {padding:24px 4px 4px;border-top:1px solid rgba(128,128,128,.22);font-size:.78rem;opacity:.65;line-height:1.55;}
.market-strip {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:12px 0 24px;}
@media (max-width: 1000px) {.hero{padding:42px 28px;min-height:auto}.hero-copy{padding-right:0}.hero h1{font-size:2.8rem}.market-card{position:relative;right:auto;top:auto;width:auto;margin-top:35px}.feature-grid{grid-template-columns:1fr}.proofbar{grid-template-columns:1fr 1fr}}
</style>
""", unsafe_allow_html=True)


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "paper_trading.db"

CATEGORY_LISTS = {
    "Top 35": ["NVDA","TSLA","AAPL","AMD","AMZN","SOFI","PLTR","INTC","F","BAC","MU","NIO","MARA","RIVN","LCID","T","PFE","CCL","AAL","SNAP","MSFT","META","GOOGL","NFLX","AVGO","QCOM","CSCO","ORCL","CRM","UBER","SHOP","COIN","HOOD","PYPL","XYZ"],
    "Magnificent 7": ["AAPL","MSFT","AMZN","GOOGL","META","NVDA","TSLA"],
    "Dividend Kings": [
        "ABM","ADP","AWR","BDX","BKH","CINF","CL","CWT","DOV","EMR",
        "FRT","FUL","GPC","GRC","HRL","JNJ","KMB","KO","LANC","LOW",
        "MMM","MO","NDSN","NFG","NWN","PEP","PG","PH","SCL","SJW",
        "SPGI","SWK","TGT","TNC","UVV"
    ],
    "Top Tech": [
        "NVDA","AAPL","MSFT","AVGO","ORCL","CRM","AMD","CSCO","IBM","QCOM",
        "ADBE","NOW","INTU","TXN","AMAT","MU","LRCX","KLAC","PANW","CRWD",
        "PLTR","SNPS","CDNS","ANET","DELL"
    ],
    "Warren Buffett": [
        "AAPL","AXP","KO","BAC","CVX","OXY","GOOGL","CB","MCO","KHC","DVA","KR","SIRI","DAL","VRSN","COF","NYT","ALLY","GOOG","LLYVK","LEN","NUE","LLYVA","LPX","STZ","NVR","M","LEN-B","JEF"
    ],
    "Semiconductors": [
        "NVDA","AMD","AVGO","MU","INTC","QCOM","TXN","AMAT","LRCX","KLAC",
        "MRVL","ARM","TSM","ASML","NXPI","ADI","MCHP","ON","MPWR","SMCI"
    ],
    "Space Stocks": [
        "RKLB","LUNR","RDW","ASTS","PL","BKSY","SIDU","SATL","IRDM","SPIR",
        "VSAT","GSAT","MNTS","ASTR","MAXR"
    ],
}

BUFFETT_13F_REPORT_DATE = "March 31, 2026"
BUFFETT_PORTFOLIO_WEIGHTS = {
    "AAPL": 21.99,
    "AXP": 17.43,
    "KO": 11.56,
    "BAC": 9.52,
    "CVX": 6.64,
    "OXY": 6.55,
    "GOOGL": 5.93,
    "CB": 4.24,
    "MCO": 4.09,
    "KHC": 2.78,
    "DVA": 1.76,
    "KR": 1.38,
    "SIRI": 1.09,
    "DAL": 1.01,
    "VRSN": 0.85,
    "COF": 0.50,
    "NYT": 0.48,
    "ALLY": 0.43,
    "GOOG": 0.39,
    "LLYVK": 0.38,
    "LEN": 0.33,
    "NUE": 0.25,
    "LLYVA": 0.17,
    "LPX": 0.16,
    "STZ": 0.04,
    "NVR": 0.03,
    "M": 0.02,
    "LEN-B": 0.01,
    "JEF": 0.01
}

SECTOR_PE_DEFAULTS = {
    "Technology": 30.0, "Communication Services": 24.0,
    "Consumer Cyclical": 24.0, "Consumer Defensive": 22.0,
    "Financial Services": 14.0, "Healthcare": 22.0,
    "Industrials": 20.0, "Energy": 12.0, "Utilities": 18.0,
    "Real Estate": 18.0, "Basic Materials": 16.0, "Unknown": 20.0,
}
INDUSTRY_PE_OVERRIDES = {
    "Semiconductors": 35.0, "Semiconductor Equipment & Materials": 30.0,
    "Software - Infrastructure": 30.0, "Software - Application": 30.0,
    "Internet Content & Information": 28.0, "Banks - Diversified": 13.0,
    "Banks - Regional": 12.0, "Oil & Gas Integrated": 12.0,
    "Oil & Gas E&P": 11.0, "Drug Manufacturers - General": 20.0,
    "Medical Devices": 24.0, "REIT - Retail": 17.0, "REIT - Industrial": 20.0,
}


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        con.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            action TEXT NOT NULL,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            asset_type TEXT NOT NULL DEFAULT 'Stock',
            multiplier REAL NOT NULL DEFAULT 1,
            description TEXT NOT NULL DEFAULT ''
        )""")
        existing_columns = {row[1] for row in con.execute("PRAGMA table_info(trades)").fetchall()}
        if "asset_type" not in existing_columns:
            con.execute("ALTER TABLE trades ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'Stock'")
        if "multiplier" not in existing_columns:
            con.execute("ALTER TABLE trades ADD COLUMN multiplier REAL NOT NULL DEFAULT 1")
        if "description" not in existing_columns:
            con.execute("ALTER TABLE trades ADD COLUMN description TEXT NOT NULL DEFAULT ''")
        con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('starting_cash','100000')")
        con.commit()


def sf(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        result = float(value)
        return None if math.isnan(result) or math.isinf(result) else result
    except Exception:
        return None


def normalize_signal(value):
    """Use BUY instead of BUY everywhere in the application."""
    signal = str(value or "").strip().upper()
    return "BUY" if signal == "BUY" else value


@st.cache_data(ttl=900, show_spinner=False)
def get_info(ticker: str):
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception:
        info = {}
    try:
        fast = dict(t.fast_info or {})
    except Exception:
        fast = {}
    if not info.get("currentPrice"):
        info["currentPrice"] = fast.get("last_price")
    return info



KNOWN_SECURITY_NAMES = {
    "MU": "Micron Technology, Inc.",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla, Inc.",
    "AMZN": "Amazon.com, Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "GOOGL": "Alphabet Inc.",
    "GOOG": "Alphabet Inc.",
    "META": "Meta Platforms, Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "SOFI": "SoFi Technologies, Inc.",
    "INTC": "Intel Corporation",
    "F": "Ford Motor Company",
    "BAC": "Bank of America Corporation",
    "NIO": "NIO Inc.",
    "MARA": "MARA Holdings, Inc.",
    "RIVN": "Rivian Automotive, Inc.",
    "T": "AT&T Inc.",
}

@st.cache_data(ttl=900, show_spinner=False)
def company_name(ticker: str):
    """Return the real security/company name, or an empty string when unavailable.

    Never return the ticker as the name; doing so caused displays such as "MU MU".
    """
    symbol = str(ticker or "").upper().strip()
    if not symbol:
        return ""

    candidates = []
    try:
        info = get_info(symbol)
        candidates.extend([info.get("longName"), info.get("shortName"), info.get("displayName")])
    except Exception:
        pass

    # Yahoo search is often more reliable than Ticker.info for resolving names.
    try:
        search = yf.Search(symbol, max_results=8, news_count=0)
        for quote in getattr(search, "quotes", []) or []:
            if str(quote.get("symbol", "")).upper() == symbol:
                candidates.extend([quote.get("longname"), quote.get("shortname"), quote.get("name")])
                break
    except Exception:
        pass

    for candidate in candidates:
        name = str(candidate or "").strip()
        if name and name.upper() != symbol:
            return name

    # Stable fallback for frequently used symbols when Yahoo omits name metadata.
    return KNOWN_SECURITY_NAMES.get(symbol, "")


def symbol_company(ticker: str):
    symbol = str(ticker or "").upper().strip()
    if not symbol:
        return ""
    name = company_name(symbol)
    return f"{symbol} [{name}]" if name else symbol


@st.cache_data(ttl=900, show_spinner=False)
def get_history(ticker: str, period="2y", interval="1d"):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise ValueError(f"No price history returned for {ticker}.")
    return df.dropna(how="all")


@st.cache_data(ttl=3600, show_spinner=False)
def get_quarterly_eps(ticker: str):
    t = yf.Ticker(ticker)
    for attr in ("quarterly_income_stmt", "quarterly_financials"):
        try:
            statement = getattr(t, attr)
        except Exception:
            continue
        if statement is None or statement.empty:
            continue
        for row in ("Diluted EPS", "Basic EPS", "DilutedEPS", "BasicEPS", "Normalized EPS"):
            if row in statement.index:
                s = pd.to_numeric(statement.loc[row], errors="coerce").dropna()
                s.index = pd.to_datetime(s.index)
                return s[~s.index.duplicated(keep="last")].sort_index()
    return pd.Series(dtype=float)


def eps_growth(q):
    q = q.dropna().sort_index()
    if len(q) < 8:
        return None
    latest = q.tail(4).sum()
    prior = q.iloc[-8:-4].sum()
    return None if latest <= 0 or prior <= 0 else (latest / prior - 1) * 100


def valuation(ticker: str, manual_growth=None, manual_pe=None):
    info = get_info(ticker)
    q = get_quarterly_eps(ticker)
    current = sf(info.get("currentPrice")) or sf(info.get("regularMarketPrice"))
    trailing = sf(info.get("trailingEps")) or (sf(q.tail(4).sum()) if not q.empty else None)
    forward = sf(info.get("forwardEps"))
    book = sf(info.get("bookValue"))
    pe = manual_pe or sf(info.get("trailingPE"))
    growth = manual_growth if manual_growth is not None else eps_growth(q)

    methods = {}
    if forward and pe and forward > 0 and pe > 0:
        methods["Forward EPS × selected P/E"] = forward * pe
    if trailing and pe and trailing > 0 and pe > 0:
        methods["Trailing EPS × selected P/E"] = trailing * pe
    if forward and growth and forward > 0 and growth > 0:
        methods["PEG = 1 value"] = forward * growth
    if trailing and book and trailing > 0 and book > 0:
        methods["Graham value"] = math.sqrt(22.5 * trailing * book)
    valid = [x for x in methods.values() if 0 < x < 100000]
    original = sum(valid) / len(valid) if valid else None

    sector = info.get("sector") or "Unknown"
    industry = info.get("industry") or "Unknown"
    relative_pe = INDUSTRY_PE_OVERRIDES.get(industry, SECTOR_PE_DEFAULTS.get(sector, 20.0))
    relative_eps = forward if forward and forward > 0 else trailing
    relative = relative_eps * relative_pe if relative_eps and relative_eps > 0 else None

    annual_div = sf(info.get("dividendRate")) or 0.0
    div_yield = annual_div / current * 100 if current else 0.0
    low52 = sf(info.get("fiftyTwoWeekLow"))
    high52 = sf(info.get("fiftyTwoWeekHigh"))

    discount = ((original - current) / original * 100) if original and current else None
    score = 50
    if discount is not None:
        score += max(-30, min(30, discount))
    if growth is not None:
        score += max(-10, min(10, growth / 3))
    score = int(max(0, min(100, round(score))))
    signal = "BUY" if score >= 65 else "HOLD" if score >= 45 else "SELL"

    return {
        "Ticker": ticker, "Company Name": info.get("longName") or info.get("shortName") or ticker, "Price": current, "Original Fair Value": original,
        "Relative Fair Value": relative, "Score": score, "Signal": normalize_signal(signal),
        "P/E": pe, "Trailing EPS": trailing, "Forward EPS": forward,
        "EPS Growth %": growth, "Annual Dividend": annual_div,
        "Dividend Yield %": div_yield, "52W Low": low52, "52W High": high52,
        "Sector": sector, "Industry": industry, "Relative P/E": relative_pe,
        "Methods": methods, "Quarterly EPS": q,
    }


@st.cache_data(ttl=1800, show_spinner=False)
def scan_group(tickers_tuple):
    rows = []
    for ticker in tickers_tuple:
        try:
            v = valuation(ticker)
            rows.append({k: v[k] for k in [
                "Ticker", "Company Name", "Price", "Original Fair Value", "Relative Fair Value", "Score", "Signal",
                "P/E", "Forward EPS", "Dividend Yield %", "52W Low", "52W High"
            ]})
        except Exception:
            rows.append({"Ticker": ticker, "Company Name": company_name(ticker), "Signal": "DATA ERROR"})
    result = pd.DataFrame(rows)
    if "Signal" in result.columns:
        result["Signal"] = result["Signal"].map(normalize_signal)
    return result


def calculate_rsi(close: pd.Series, periods=14):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/periods, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/periods, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def chart_figure(ticker, v, history_months):
    months_to_period = {1: "6mo", 3: "1y", 6: "1y"}
    full = get_history(ticker, months_to_period[history_months], "1d").copy()
    close = full["Close"].astype(float)
    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    upper, lower = mid + 2 * std, mid - 2 * std
    rsi = calculate_rsi(close)
    cutoff = full.index.max() - pd.DateOffset(months=history_months)
    df = full.loc[full.index >= cutoff]
    mid, upper, lower, rsi = mid.loc[df.index], upper.loc[df.index], lower.loc[df.index], rsi.loc[df.index]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.68, 0.32], vertical_spacing=0.05,
        subplot_titles=("Price & Bollinger Bands", "RSI Momentum (14)")
    )
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=upper, name="BB Upper", line=dict(width=5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=mid, name="BB Mid", line=dict(width=5, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=lower, name="BB Lower", line=dict(width=5), fill="tonexty", fillcolor="rgba(128,128,128,0.14)"), row=1, col=1)

    # Show the latest dollar amount at the right end of each Bollinger Band line.
    last_x = df.index[-1]
    for series, label in [(upper, "Upper"), (mid, "Mid"), (lower, "Lower")]:
        clean = series.dropna()
        if not clean.empty:
            latest_value = float(clean.iloc[-1])
            fig.add_annotation(
                x=last_x, y=latest_value, text=f"{label} ${latest_value:,.2f}",
                showarrow=False, xanchor="left", xshift=10,
                bgcolor="rgba(255,255,255,0.82)", borderpad=3,
                font=dict(size=17), row=1, col=1,
            )

    # Mark the live/current price with a subtle light-green dotted reference line.
    current_price = sf(v.get("Current Price"))
    if not current_price or current_price <= 0:
        current_price = float(df["Close"].dropna().iloc[-1])
    fig.add_hline(
        y=current_price, line_dash="dash", line_width=3, line_color="#90EE90",
        annotation_text=f"Current Price ${current_price:,.2f}",
        annotation_position="right", row=1, col=1
    )

    original_fv = sf(v.get("Original Fair Value"))
    relative_fv = sf(v.get("Relative Fair Value"))

    # Keep Relative FV off the chart when it is an outlier versus Original FV.
    # A 30% maximum difference keeps the price scale useful while preserving
    # the underlying Relative FV calculation elsewhere in the app.
    relative_fv_for_chart = None
    if original_fv and original_fv > 0 and relative_fv and relative_fv > 0:
        relative_gap_pct = abs(relative_fv - original_fv) / original_fv
        if relative_gap_pct <= 0.30:
            relative_fv_for_chart = relative_fv

    for label, value, dash in [
        ("Original FV", original_fv, "dash"),
        ("Relative FV", relative_fv_for_chart, "dot"),
    ]:
        if value:
            fig.add_hline(
                y=value, line_dash=dash, line_width=3,
                annotation_text=f"{label} ${value:,.2f}",
                annotation_position="right", row=1, col=1
            )

    # Make RSI visually distinct with momentum zones and a prominent live reading.
    fig.add_hrect(
        y0=70, y1=100, fillcolor="rgba(220, 53, 69, 0.16)", line_width=0,
        annotation_text="OVERBOUGHT", annotation_position="top left", row=2, col=1
    )
    fig.add_hrect(
        y0=30, y1=70, fillcolor="rgba(108, 117, 125, 0.035)", line_width=0,
        row=2, col=1
    )
    fig.add_hrect(
        y0=0, y1=30, fillcolor="rgba(25, 135, 84, 0.16)", line_width=0,
        annotation_text="OVERSOLD", annotation_position="bottom left", row=2, col=1
    )
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi, name="RSI 14",
        mode="lines", line=dict(width=3.5, color="#7C3AED"),
        hovertemplate="RSI %{y:.1f}<extra></extra>"
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_width=2, line_color="#DC3545",
                  annotation_text="70", annotation_position="right", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", line_width=1.5, line_color="#6C757D",
                  annotation_text="50", annotation_position="right", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_width=2, line_color="#198754",
                  annotation_text="30", annotation_position="right", row=2, col=1)
    latest_rsi = sf(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else None
    if latest_rsi is not None:
        marker_color = "#DC3545" if latest_rsi >= 70 else "#198754" if latest_rsi <= 30 else "#7C3AED"
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[latest_rsi], name="Current RSI",
            mode="markers+text", text=[f"  {latest_rsi:.1f}"], textposition="middle right",
            marker=dict(size=13, color=marker_color, line=dict(width=2, color="white")),
            textfont=dict(size=15, color=marker_color),
            hovertemplate=f"Current RSI: {latest_rsi:.1f}<extra></extra>",
            showlegend=False
        ), row=2, col=1)

    values = pd.concat([close.loc[df.index], upper, lower]).dropna()
    extras = [x for x in (original_fv, relative_fv_for_chart) if x]
    if not values.empty:
        ymin = min([values.min()] + extras)
        ymax = max([values.max()] + extras)
        pad = max((ymax - ymin) * 0.08, ymax * 0.01)
        axis_min, axis_max = ymin - pad, ymax + pad

        # Keep the price scale clean when fair value is far from the market price.
        # Plotly will show roughly five to seven major price levels rather than
        # filling the large gap with many intermediate labels.
        span = max(axis_max - axis_min, 0.01)
        raw_step = span / 6
        magnitude = 10 ** math.floor(math.log10(raw_step))
        normalized = raw_step / magnitude
        nice_factor = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
        clean_tick_step = nice_factor * magnitude

        fig.update_yaxes(
            range=[axis_min, axis_max], side="right", row=1, col=1,
            tickmode="linear", dtick=clean_tick_step,
            tickprefix="$", tickformat=",.2f",
            tickfont=dict(size=16), title_text="Price"
        )
    fig.update_yaxes(
        range=[0, 100], side="right", row=2, col=1,
        tickmode="array", tickvals=[0, 20, 30, 40, 50, 60, 70, 80, 100],
        gridcolor="rgba(128,128,128,0.18)", title_text="RSI"
    )
    fig.update_layout(
        title=f"{ticker} {v.get('Company Name', ticker)} — Price, Bollinger Bands, Fair Values and RSI",
        height=1120, xaxis_rangeslider_visible=False, hovermode="x unified",
        dragmode="zoom",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=245, t=90, b=30),
    )
    return fig


def option_delta_estimate(spot, strike, dte, iv, option_type):
    if not all([spot, strike, dte, iv]) or dte <= 0 or iv <= 0:
        return None
    t = dte / 365
    r = 0.04
    d1 = (math.log(spot / strike) + (r + 0.5 * iv**2) * t) / (iv * math.sqrt(t))
    cdf = NormalDist().cdf(d1)
    return cdf if option_type == "calls" else cdf - 1


@st.cache_data(ttl=300, show_spinner=False)
def option_expirations(ticker):
    return list(yf.Ticker(ticker).options)


@st.cache_data(ttl=300, show_spinner=False)
def option_chain(ticker, expiration, side):
    chain = yf.Ticker(ticker).option_chain(expiration)
    return (chain.calls if side == "calls" else chain.puts).copy()


def load_trades():
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", con)


def starting_cash():
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT value FROM settings WHERE key='starting_cash'").fetchone()
    return float(row[0]) if row else 100000.0


def save_starting_cash(value):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('starting_cash',?)", (str(value),))
        con.commit()


def portfolio_summary(trades):
    cash = starting_cash()
    realized = 0.0
    positions = {}

    for _, r in trades.sort_values("id").iterrows():
        ticker = str(r.get("ticker", "")).upper().strip()
        asset_type = str(r.get("asset_type", "Stock") or "Stock")
        description = str(r.get("description", "") or "")
        quantity = float(r.get("shares", 0) or 0)
        price = float(r.get("price", 0) or 0)
        multiplier = float(r.get("multiplier", 1) or 1)
        key = (asset_type, ticker, multiplier, description)
        pos = positions.setdefault(key, {"quantity": 0.0, "cost": 0.0, "last_price": price})

        if str(r.get("action", "")).upper() == "BUY":
            cash -= quantity * price * multiplier
            pos["quantity"] += quantity
            pos["cost"] += quantity * price * multiplier
        else:
            avg_contract_cost = pos["cost"] / pos["quantity"] if pos["quantity"] else 0
            sold = min(quantity, pos["quantity"])
            realized += sold * ((price * multiplier) - avg_contract_cost)
            pos["quantity"] -= sold
            pos["cost"] -= sold * avg_contract_cost
            cash += sold * price * multiplier
        pos["last_price"] = price

    rows, market_value, unrealized = [], 0.0, 0.0
    for (asset_type, ticker, multiplier, description), pos in positions.items():
        if pos["quantity"] <= 1e-9:
            continue

        current_price = pos["last_price"]
        try:
            quoted_price = quick_quote(ticker)["price"]
            if quoted_price is not None:
                current_price = float(quoted_price)
        except Exception:
            pass

        avg_price = pos["cost"] / (pos["quantity"] * multiplier)
        mv = pos["quantity"] * current_price * multiplier
        pnl = pos["quantity"] * (current_price - avg_price) * multiplier
        market_value += mv
        unrealized += pnl
        rows.append({
            "Asset Type": asset_type,
            "Symbol": ticker,
            "Company Name": company_name(ticker),
            "Description": description,
            "Quantity": pos["quantity"],
            "Multiplier": multiplier,
            "Avg Price": avg_price,
            "Current Price": current_price,
            "Market Value": mv,
            "Unrealized P&L": pnl,
        })

    account = cash + market_value
    return cash, market_value, account, realized, unrealized, pd.DataFrame(rows)



@st.cache_data(ttl=180, show_spinner=False)
def quick_quote(ticker: str):
    ticker = ticker.upper().strip()
    info = get_info(ticker)
    hist = get_history(ticker, period="5d", interval="1d")
    closes = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    price = sf(info.get("currentPrice")) or sf(info.get("regularMarketPrice")) or (sf(closes.iloc[-1]) if not closes.empty else None)
    previous = sf(info.get("previousClose")) or (sf(closes.iloc[-2]) if len(closes) > 1 else None)
    change = (price - previous) if price is not None and previous is not None else None
    change_pct = (change / previous * 100) if change is not None and previous else None
    day_low = sf(info.get("dayLow")) or sf(info.get("regularMarketDayLow"))
    day_high = sf(info.get("dayHigh")) or sf(info.get("regularMarketDayHigh"))
    earnings_ts = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
    earnings_date = None
    if earnings_ts:
        try:
            earnings_date = datetime.fromtimestamp(int(earnings_ts)).strftime("%b %d, %Y")
        except Exception:
            earnings_date = None
    return {
        "ticker": ticker, "name": company_name(ticker),
        "exchange": info.get("fullExchangeName") or info.get("exchange") or "",
        "currency": info.get("currency") or "USD",
        "price": price, "change": change, "change_pct": change_pct,
        "previous_close": previous,
        "open": sf(info.get("open")) or sf(info.get("regularMarketOpen")),
        "bid": sf(info.get("bid")), "bid_size": sf(info.get("bidSize")),
        "ask": sf(info.get("ask")), "ask_size": sf(info.get("askSize")),
        "day_low": day_low, "day_high": day_high,
        "week52_low": sf(info.get("fiftyTwoWeekLow")),
        "week52_high": sf(info.get("fiftyTwoWeekHigh")),
        "volume": sf(info.get("volume")) or sf(info.get("regularMarketVolume")),
        "avg_volume": sf(info.get("averageVolume")) or sf(info.get("averageDailyVolume3Month")),
        "market_cap": sf(info.get("marketCap")), "beta": sf(info.get("beta")),
        "pe": sf(info.get("trailingPE")), "eps": sf(info.get("trailingEps")),
        "earnings_date": earnings_date,
        "dividend_rate": sf(info.get("dividendRate")),
        "dividend_yield": (sf(info.get("dividendYield")) or 0) * 100,
    }


@st.cache_data(ttl=300, show_spinner=False)
def most_active_quotes():
    fallback = ["NVDA","TSLA","AAPL","AMD","AMZN","SOFI","PLTR","INTC","F","BAC","MU","NIO","MARA","RIVN","T"]
    symbols = []
    try:
        result = yf.screen("most_actives", count=25)
        quotes = result.get("quotes", []) if isinstance(result, dict) else []
        symbols = [q.get("symbol") for q in quotes if q.get("symbol") and q.get("quoteType") in (None, "EQUITY")]
    except Exception:
        symbols = fallback
    symbols = list(dict.fromkeys(symbols + fallback))[:25]
    rows = []
    for symbol in symbols:
        try:
            rows.append(quick_quote(symbol))
        except Exception:
            continue
    rows.sort(key=lambda r: r.get("volume") or 0, reverse=True)
    return rows[:10]


def money(value):
    return "N/A" if value is None else f"${value:,.2f}"


def compact_number(value):
    if value is None:
        return "N/A"
    for unit, divisor in (("T",1e12),("B",1e9),("M",1e6),("K",1e3)):
        if abs(value) >= divisor:
            return f"{value/divisor:,.2f}{unit}"
    return f"{value:,.0f}"

def render_navigation(key_prefix="nav"):
    nav_columns = st.columns(len(section_names), gap="small")
    for nav_col, (icon, section_name) in zip(nav_columns, section_names):
        with nav_col:
            if st.button(
                f"{icon}  {section_name}",
                key=f"{key_prefix}_{section_name}",
                use_container_width=False,
                type="primary" if st.session_state.active_section == section_name else "secondary",
            ):
                st.session_state.active_section = section_name
                st.rerun()

def render_homepage():
    st.markdown('<div class="section-title">MAJOR MARKETS</div><div class="section-copy"></div>', unsafe_allow_html=True)
    market_assets = [("S&P 500","^GSPC"),("S&P 500 E-mini Futures","ES=F"),("Nasdaq","^IXIC"),("Dow","^DJI"),("Bitcoin","BTC-USD"),("WTI Oil","CL=F")]
    market_cols = st.columns(6)
    for col, (label, symbol) in zip(market_cols, market_assets):
        with col:
            try:
                mq = quick_quote(symbol)
                change = mq["change"]
                change_pct = mq.get("change_pct")
                name_color = "#16a34a" if change is not None and change > 0 else "#dc2626" if change is not None and change < 0 else "#6b7280"
                delta_text = "N/A" if change is None else f"{change:+.2f}" + (f" ({change_pct:+.2f}%)" if change_pct is not None else "")
                st.markdown(
                    f"""
                    <div style="padding:.55rem .65rem;border:1px solid rgba(128,128,128,.20);border-radius:12px;min-height:108px">
                      <div style="font-size:.78rem;font-weight:800;color:{name_color};line-height:1.15;min-height:2rem">{label.upper()}</div>
                      <div style="font-size:1.12rem;font-weight:800;margin-top:.2rem">{money(mq['price'])}</div>
                      <div style="font-size:.76rem;margin-top:.15rem;color:{name_color};font-weight:700">{delta_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception:
                st.markdown(
                    f"""
                    <div style="padding:.55rem .65rem;border:1px solid rgba(128,128,128,.20);border-radius:12px;min-height:108px">
                      <div style="font-size:.78rem;font-weight:800;color:#6b7280;line-height:1.15;min-height:2rem">{label.upper()}</div>
                      <div style="font-size:.95rem;font-weight:700;margin-top:.35rem">Unavailable</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("""
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">Research • Valuation • Technicals</span>
        <h1>STOCK FAIR VALUE TOOL</h1>
        <p>Check stocks, Bitcoin, major indexes and oil, then move directly into earnings-based valuation and technical analysis.</p>
      </div>
      <div class="market-card">
        <div class="ticker"><div><div style="opacity:.62;font-size:.78rem">MARKET INTELLIGENCE</div><b>Quote → Valuation → Decision</b></div></div>
        <svg class="spark" viewBox="0 0 340 160" preserveAspectRatio="none" aria-label="Illustrative market chart">
          <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#22d3ee" stop-opacity=".42"/><stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/></linearGradient></defs>
          <path d="M0 130 C28 124,42 132,66 111 S105 117,128 89 S171 103,197 68 S236 79,260 47 S302 53,340 20 L340 160 L0 160 Z" fill="url(#area)"/>
          <path d="M0 130 C28 124,42 132,66 111 S105 117,128 89 S171 103,197 68 S236 79,260 47 S302 53,340 20" fill="none" stroke="#67e8f9" stroke-width="4" stroke-linecap="round"/>
        </svg>
        <div class="statrow"><div class="stat">LIVE QUOTES<b>Stocks</b></div><div class="stat">MARKETS<b>Indexes</b></div><div class="stat">ALTERNATIVES<b>BTC + Oil</b></div></div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    render_navigation("home_nav")

    st.markdown('<div class="section-title">Instant market quote</div><div class="section-copy">Enter a stock symbol for a Yahoo Finance-style snapshot, then open the complete analysis.</div>', unsafe_allow_html=True)
    q1, q2 = st.columns([5,1])
    with q1:
        home_ticker = st.text_input("Stock symbol", value=st.session_state.get("home_quote_ticker", ""), label_visibility="collapsed", placeholder="Enter ticker — AAPL, MSFT, KO...").upper().strip()
    with q2:
        get_quote = st.button("Get Quote", type="primary", use_container_width=True, key="home_get_quote")
    if get_quote and home_ticker:
        st.session_state.home_quote_ticker = home_ticker
    quote_ticker = st.session_state.get("home_quote_ticker", "")
    if quote_ticker:
        try:
            q = quick_quote(quote_ticker)
            change_text = "N/A" if q["change"] is None else f'{q["change"]:+.2f}'
            change_pct_text = "N/A" if q["change_pct"] is None else f'{q["change_pct"]:+.2f}%'
            exchange_line = " • ".join(x for x in [q.get("exchange"), q.get("currency")] if x)
            st.markdown(
                f"""
                <div style="padding:22px 24px;border:1px solid rgba(128,128,128,.24);border-radius:16px;background:rgba(128,128,128,.035);margin:8px 0 18px">
                  <div style="font-size:1.55rem;font-weight:800;letter-spacing:-.02em">{symbol_company(q['ticker'])}</div>
                  <div style="opacity:.65;font-size:.84rem;margin-top:2px">{exchange_line}</div>
                  <div style="display:flex;align-items:baseline;gap:14px;margin-top:14px;flex-wrap:wrap">
                    <span style="font-size:2.75rem;font-weight:850;letter-spacing:-.045em">{money(q['price'])}</span>
                    <span style="font-size:1.08rem;font-weight:750">{change_text} ({change_pct_text})</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            left_stats, right_stats = st.columns(2, gap="large")
            with left_stats:
                left_rows = [
                    ("Previous Close", money(q["previous_close"])),
                    ("Open", money(q["open"])),
                    ("Bid", "N/A" if q["bid"] is None else f'{money(q["bid"])} x {int(q["bid_size"] or 0)}'),
                    ("Ask", "N/A" if q["ask"] is None else f'{money(q["ask"])} x {int(q["ask_size"] or 0)}'),
                    ("Day's Range", "N/A" if q["day_low"] is None or q["day_high"] is None else f'{money(q["day_low"])} - {money(q["day_high"])}'),
                    ("52 Week Range", "N/A" if q["week52_low"] is None or q["week52_high"] is None else f'{money(q["week52_low"])} - {money(q["week52_high"])}'),
                ]
                for label, value in left_rows:
                    st.markdown(f"**{label}** <span style='float:right'>{value}</span><hr style='margin:.38rem 0;border:none;border-top:1px solid rgba(128,128,128,.18)'>", unsafe_allow_html=True)
            with right_stats:
                dividend_text = "N/A" if q["dividend_rate"] is None else f'{money(q["dividend_rate"])} ({q["dividend_yield"]:.2f}%)'
                right_rows = [
                    ("Volume", compact_number(q["volume"])),
                    ("Avg. Volume", compact_number(q["avg_volume"])),
                    ("Market Cap", compact_number(q["market_cap"])),
                    ("Beta (5Y Monthly)", "N/A" if q["beta"] is None else f'{q["beta"]:.2f}'),
                    ("PE Ratio (TTM)", "N/A" if q["pe"] is None else f'{q["pe"]:.2f}'),
                    ("EPS (TTM)", "N/A" if q["eps"] is None else money(q["eps"])),
                    ("Earnings Date", q["earnings_date"] or "N/A"),
                    ("Forward Dividend & Yield", dividend_text),
                ]
                for label, value in right_rows:
                    st.markdown(f"**{label}** <span style='float:right'>{value}</span><hr style='margin:.38rem 0;border:none;border-top:1px solid rgba(128,128,128,.18)'>", unsafe_allow_html=True)
            if st.button(f'Analyze {q["ticker"]} in Full Dashboard →', type="primary", key="home_analyze_quote"):
                st.session_state.selected_ticker = q["ticker"]
                st.session_state.options_ticker = q["ticker"]
                st.session_state.active_section = "Price vs EPS"
                st.rerun()
        except Exception as exc:
            st.warning(f"Quote unavailable for {quote_ticker}: {exc}")

    st.markdown('<div class="section-title">Top 10 most actively traded</div><div class="section-copy">Ranked by reported trading volume. Click a symbol to update the instant quote.</div>', unsafe_allow_html=True)
    try:
        active = most_active_quotes()
        for rank, row in enumerate(active, 1):
            a,b,c,d,e = st.columns([.5,1.2,3,1.4,1.2])
            a.write(f"**{rank}**")
            if b.button(symbol_company(row["ticker"]), key=f"active_{rank}_{row['ticker']}", use_container_width=True):
                st.session_state.home_quote_ticker = row["ticker"]
                st.rerun()
            c.write(row["name"] or "Name unavailable")
            d.write(money(row["price"]))
            pct = row.get("change_pct")
            e.write("N/A" if pct is None else f"{pct:+.2f}%")
    except Exception as exc:
        st.info(f"Most-active data is temporarily unavailable: {exc}")


init_db()
for key, value in {
    "selected_ticker": "", "options_ticker": "", "manual_growth": "", "manual_pe": ""
}.items():
    st.session_state.setdefault(key, value)

# Apply a watchlist selection before Streamlit creates ticker input widgets.
# This avoids changing a widget-backed session key after the widget exists.
if "pending_watchlist_ticker" in st.session_state:
    pending_ticker = str(st.session_state.pop("pending_watchlist_ticker")).upper().strip()
    if pending_ticker:
        st.session_state.selected_ticker = pending_ticker
        st.session_state.options_ticker = pending_ticker
        st.session_state.active_section = "Price vs EPS"

st.session_state.setdefault("active_section", "Home")

section_names = [
    ("⌂", "Home"),
    ("📈", "Price vs EPS"),
    ("📋", "Watchlists"),
    ("💼", "Paper Trading"),
    ("🧪", "Backtesting"),
    ("🔎", "Options Finder"),
]
active_section = st.session_state.active_section
if active_section != "Home":
    st.markdown('<div style="height:2.75rem"></div>', unsafe_allow_html=True)
    render_navigation("nav")

ticker = st.session_state.selected_ticker.upper().strip()
history_months = 3
mg_text = st.session_state.manual_growth
pe_text = st.session_state.manual_pe

if active_section == "Home":
    render_homepage()
else:
    st.caption("Yahoo Finance data is unofficial and may be delayed or rate-limited.")

if active_section == "Price vs EPS":
    st.subheader("Price vs EPS Analysis")
    with st.form("price_eps_symbol_form", clear_on_submit=False):
        symbol_col, button_col = st.columns([4, 1])
        with symbol_col:
            entered_symbol = st.text_input(
                "Enter Symbol to Analyze",
                value=ticker,
                placeholder="AAPL, MSFT, NVDA...",
            ).upper().strip()
        with button_col:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            analyze_symbol = st.form_submit_button(
                "Analyze",
                type="primary",
                use_container_width=True,
            )

    if analyze_symbol:
        if entered_symbol:
            st.session_state.selected_ticker = entered_symbol
            st.session_state.options_ticker = entered_symbol
            st.rerun()
        else:
            st.warning("Enter a stock symbol to analyze.")

    if ticker:
        try:
            mg = float(mg_text) if mg_text.strip() else None
            mpe = float(pe_text) if pe_text.strip() else None
            with st.spinner(f"Loading {ticker}..."):
                v = valuation(ticker, mg, mpe)
            st.markdown(f"### {symbol_company(v['Ticker'])}")
            cols = st.columns(6)
            metrics = [
                ("Price", v["Price"], "$"), ("Original FV", v["Original Fair Value"], "$"),
                ("Relative FV", v["Relative Fair Value"], "$"), ("Score", v["Score"], ""),
                ("Signal", normalize_signal(v["Signal"]), ""), ("Dividend Yield", v["Dividend Yield %"], "%"),
            ]
            for c, (label, value, unit) in zip(cols, metrics):
                if isinstance(value, (int, float)) and value is not None:
                    text = f"${value:,.2f}" if unit == "$" else f"{value:,.2f}%" if unit == "%" else f"{value}"
                else:
                    text = value or "N/A"
                c.metric(label, text)
            st.plotly_chart(
                chart_figure(ticker, v, history_months),
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "scrollZoom": True,
                    "displayModeBar": True,
                    "modeBarButtonsToAdd": ["drawline", "eraseshape"],
                    "responsive": True,
                },
            )
            left, right = st.columns(2)
            with left:
                st.subheader("Valuation methods")
                methods_df = pd.DataFrame([{"Method": k, "Value": val} for k, val in v["Methods"].items()])
                st.dataframe(methods_df, use_container_width=True, hide_index=True, column_config={"Value": st.column_config.NumberColumn(format="$%.2f")})
            with right:
                st.subheader("Fundamentals")
                fundamentals = pd.DataFrame({
                    "Metric": ["Sector", "Industry", "Trailing EPS", "Forward EPS", "P/E used", "EPS Growth", "Relative P/E"],
                    "Value": [v["Sector"], v["Industry"], v["Trailing EPS"], v["Forward EPS"], v["P/E"], v["EPS Growth %"], v["Relative P/E"]]
                })
                st.dataframe(fundamentals, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not analyze {ticker}: {exc}")
    else:
        st.info("Enter a symbol above, then select Analyze.")

if active_section == "Watchlists":
    st.session_state.setdefault("watchlist_category", list(CATEGORY_LISTS)[0])
    st.subheader("Watchlists")
    category_names = list(CATEGORY_LISTS)
    category_cols = st.columns(len(category_names), gap="small")
    for category_col, category_name in zip(category_cols, category_names):
        with category_col:
            if st.button(
                category_name,
                key=f"watchlist_{category_name}",
                use_container_width=True,
                type="primary" if st.session_state.watchlist_category == category_name else "secondary",
            ):
                st.session_state.watchlist_category = category_name
                st.rerun()
    category = st.session_state.watchlist_category
    tickers = CATEGORY_LISTS[category]
    with st.spinner(f"Loading {category}..."):
        watch_df = scan_group(tuple(tickers))
    if category == "Warren Buffett":
        watch_df["% of Total Portfolio"] = watch_df["Ticker"].map(BUFFETT_PORTFOLIO_WEIGHTS)
        st.caption(
            f"Portfolio percentages are based on Berkshire Hathaway's latest disclosed 13F holdings "
            f"as of {BUFFETT_13F_REPORT_DATE}. Click any row to load that ticker."
        )
    else:
        st.caption("Click any row to load that ticker directly into the chart and Options Finder.")
    watch_df = watch_df.rename(columns={"Dividend Yield %": "Div.Yield %"})
    if "Signal" in watch_df.columns:
        watch_df["Signal"] = watch_df["Signal"].map(normalize_signal)
    # Show the strongest-ranked stocks first while keeping Streamlit's
    # interactive header sorting available to the user.
    if "Score" in watch_df.columns:
        watch_df = watch_df.sort_values(by="Score", ascending=False, na_position="last").reset_index(drop=True)

    # Keep Score immediately after Price for every watchlist category.
    preferred_order = ["Ticker", "Company Name"]
    if "% of Total Portfolio" in watch_df.columns:
        preferred_order.append("% of Total Portfolio")
    preferred_order.extend([
        "Price", "Score", "Original Fair Value", "Relative Fair Value", "Signal",
        "P/E", "Forward EPS", "Div.Yield %", "52W Low", "52W High"
    ])
    remaining_columns = [col for col in watch_df.columns if col not in preferred_order]
    watch_df = watch_df[[col for col in preferred_order if col in watch_df.columns] + remaining_columns]
    watch_display_df = watch_df.copy()
    watch_display_df.insert(0, "Symbol Company", watch_display_df["Ticker"].map(symbol_company))
    watch_display_df = watch_display_df.drop(columns=["Ticker", "Company Name"], errors="ignore")

    event = st.dataframe(
        watch_display_df,
        key=f"watchlist_table_{category}",
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Symbol Company": st.column_config.TextColumn(width=260),
            "Price": st.column_config.NumberColumn(format="$%.2f", width=105),
            "Score": st.column_config.NumberColumn(width=85),
            "Original Fair Value": st.column_config.NumberColumn(format="$%.2f", width=155),
            "Relative Fair Value": st.column_config.NumberColumn(format="$%.2f", width=155),
            "Signal": st.column_config.TextColumn(width=115),
            "P/E": st.column_config.NumberColumn(format="%.2f", width=90),
            "Forward EPS": st.column_config.NumberColumn(format="%.2f", width=125),
            "% of Total Portfolio": st.column_config.NumberColumn(format="%.2f%%", width=170),
            "Div.Yield %": st.column_config.NumberColumn(format="%.2f%%", width=125),
            "52W Low": st.column_config.NumberColumn(format="$%.2f", width=105),
            "52W High": st.column_config.NumberColumn(format="$%.2f", width=105),
        }
    )
    selected_rows = event.selection.rows if event and hasattr(event, "selection") else []
    if selected_rows:
        selected = str(watch_df.iloc[selected_rows[0]]["Ticker"]).upper().strip()
        st.session_state.pending_watchlist_ticker = selected
        st.rerun()

if active_section == "Paper Trading":
    cash_col, save_col = st.columns([4, 1])
    starting_cash_text = cash_col.text_input(
        "Starting cash",
        value=f"${starting_cash():,.2f}",
        key="starting_cash_text",
        help="Enter a dollar amount, for example $100,000.00",
    )
    if save_col.button("Save starting cash", use_container_width=True):
        try:
            parsed_cash = float(starting_cash_text.replace("$", "").replace(",", "").strip())
            if parsed_cash < 0:
                raise ValueError
            save_starting_cash(parsed_cash)
            st.session_state.starting_cash_text = f"${parsed_cash:,.2f}"
            st.success("Starting cash saved.")
            st.rerun()
        except ValueError:
            st.error("Enter a valid non-negative dollar amount.")

    trades = load_trades()
    cash, mv, account, realized, unrealized, positions = portfolio_summary(trades)
    a, b, c, d, e = st.columns(5)
    a.metric("Cash", f"${cash:,.2f}")
    b.metric("Positions", f"${mv:,.2f}")
    c.metric("Account Value", f"${account:,.2f}")
    d.metric("Unrealized P&L", f"${unrealized:,.2f}")
    e.metric("Realized P&L", f"${realized:,.2f}")

    with st.expander("Paper trade entry", expanded=True):
        def render_paper_trade_entry(asset_type):
            p1, p2, p3, p4, p5 = st.columns(5)
            default_symbol = st.session_state.selected_ticker if asset_type == "Stock" else ""
            pticker = p1.text_input(
                "Symbol",
                value=default_symbol,
                key=f"paper_symbol_{asset_type}",
                placeholder="AAPL, AAPL option symbol, or ES=F",
            ).upper().strip()
            if pticker:
                resolved_name = company_name(pticker)
                st.caption(symbol_company(pticker))
            action = p2.selectbox("Action", ["BUY", "SELL"], key=f"paper_action_{asset_type}")
            quantity_label = "Shares" if asset_type == "Stock" else "Contracts"
            quantity = p3.number_input(
                quantity_label,
                min_value=0.01,
                value=1.0,
                step=1.0,
                key=f"paper_qty_{asset_type}",
            )

            default_price = 0.0
            if pticker:
                try:
                    default_price = float(quick_quote(pticker)["price"] or 0.0)
                except Exception:
                    pass
            price = p4.number_input(
                "Trade price",
                min_value=0.0,
                value=default_price,
                step=0.01,
                key=f"paper_price_{asset_type}",
            )
            trade_date = p5.date_input("Date", value=date.today(), key=f"paper_date_{asset_type}")

            d1, d2 = st.columns([1, 3])
            default_multiplier = 1.0 if asset_type == "Stock" else 100.0 if asset_type == "Option" else 50.0
            multiplier = d1.number_input(
                "Contract multiplier",
                min_value=0.01,
                value=default_multiplier,
                step=1.0,
                key=f"paper_multiplier_{asset_type}",
                help="Stocks normally use 1, equity options normally use 100, and futures vary by contract.",
            )
            description = d2.text_input(
                "Description",
                key=f"paper_description_{asset_type}",
                placeholder="Optional: AAPL 190 Call 2026-09-18 or E-mini S&P 500",
            )

            estimated_value = quantity * price * multiplier
            st.caption(f"Estimated trade value: ${estimated_value:,.2f}")

            if st.button("Save Trade", type="primary", key=f"save_paper_trade_{asset_type}", use_container_width=True):
                if not pticker:
                    st.error("Enter a symbol.")
                elif price <= 0:
                    st.error("Enter a trade price greater than zero.")
                else:
                    with sqlite3.connect(DB_PATH) as con:
                        con.execute(
                            """INSERT INTO trades
                            (trade_date, action, ticker, shares, price, asset_type, multiplier, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (trade_date.isoformat(), action, pticker, quantity, price, asset_type, multiplier, description),
                        )
                        con.commit()
                    st.success(f"{asset_type} trade saved.")
                    st.rerun()

        stock_tab, option_tab, future_tab = st.tabs(["Stock", "Option", "Future"])
        with stock_tab:
            render_paper_trade_entry("Stock")
        with option_tab:
            render_paper_trade_entry("Option")
        with future_tab:
            render_paper_trade_entry("Future")

    if not positions.empty:
        st.subheader("Open positions")
        st.dataframe(
            positions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg Price": st.column_config.NumberColumn(format="$%.2f"),
                "Current Price": st.column_config.NumberColumn(format="$%.2f"),
                "Market Value": st.column_config.NumberColumn(format="$%.2f"),
                "Unrealized P&L": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

        with st.expander("Close an open position", expanded=False):
            position_labels = []
            for idx, row in positions.reset_index(drop=True).iterrows():
                desc = f" — {row['Description']}" if str(row.get('Description', '')).strip() else ""
                position_labels.append(
                    f"{idx + 1}. {row['Asset Type']} | {row['Company Name']} ({row['Symbol']}) | Qty {row['Quantity']:g}{desc}"
                )
            selected_position_label = st.selectbox("Position", position_labels, key="close_position_select")
            selected_position_index = position_labels.index(selected_position_label)
            selected_position = positions.reset_index(drop=True).iloc[selected_position_index]
            cp1, cp2, cp3 = st.columns(3)
            close_quantity = cp1.number_input(
                "Quantity to close",
                min_value=0.01,
                max_value=float(selected_position["Quantity"]),
                value=float(selected_position["Quantity"]),
                step=1.0,
                key="close_position_quantity",
            )
            close_price = cp2.number_input(
                "Close price",
                min_value=0.01,
                value=max(float(selected_position["Current Price"]), 0.01),
                step=0.01,
                key="close_position_price",
            )
            close_date = cp3.date_input("Close date", value=date.today(), key="close_position_date")
            if st.button("Close Position", type="primary", key="close_position_button"):
                with sqlite3.connect(DB_PATH) as con:
                    con.execute(
                        """INSERT INTO trades
                        (trade_date, action, ticker, shares, price, asset_type, multiplier, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            close_date.isoformat(),
                            "SELL",
                            str(selected_position["Symbol"]),
                            float(close_quantity),
                            float(close_price),
                            str(selected_position["Asset Type"]),
                            float(selected_position["Multiplier"]),
                            str(selected_position.get("Description", "") or ""),
                        ),
                    )
                    con.commit()
                st.success("Position closed." if close_quantity >= float(selected_position["Quantity"]) else "Position partially closed.")
                st.rerun()

    st.subheader("Trade history")
    if trades.empty:
        st.info("No paper trades yet.")
    else:
        display_trades = trades.rename(columns={"shares": "quantity"}).copy()
        display_trades.insert(4, "company_name", display_trades["ticker"].map(company_name))
        display_trades.insert(4, "symbol_company", display_trades["ticker"].map(symbol_company))
        edited = st.data_editor(
            display_trades,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "symbol_company", "company_name"],
            num_rows="fixed",
            key="trade_editor",
            column_config={
                "symbol_company": st.column_config.TextColumn("Symbol Company"),
                "ticker": st.column_config.TextColumn("Ticker (data key)"),
                "company_name": st.column_config.TextColumn("Company Name"),
                "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "multiplier": st.column_config.NumberColumn("Multiplier", format="%.2f"),
            },
        )
        trade_options = {
            f"ID {int(r.id)} | {str(r.action).upper()} {float(r.quantity):g} {symbol_company(r.ticker)} @ ${float(r.price):,.2f}": int(r.id)
            for _, r in display_trades.iterrows()
        }
        selected_trade_label = st.selectbox("Selected trade", list(trade_options.keys()), key="selected_trade_action")
        selected_trade_id = trade_options[selected_trade_label]

        col1, col2, col3, col4 = st.columns(4)
        if col1.button("Save Changes", use_container_width=True):
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM trades")
                for _, r in edited.iterrows():
                    con.execute(
                        """INSERT INTO trades
                        (id, trade_date, action, ticker, shares, price, asset_type, multiplier, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            int(r.id),
                            str(r.trade_date),
                            str(r.action).upper(),
                            str(r.ticker).upper(),
                            float(r.quantity),
                            float(r.price),
                            str(r.asset_type),
                            float(r.multiplier),
                            str(r.description or ""),
                        ),
                    )
                con.commit()
            st.success("Trades updated.")
            st.rerun()

        if col2.button("Duplicate Trade", use_container_width=True):
            source = trades.loc[trades["id"] == selected_trade_id].iloc[0]
            with sqlite3.connect(DB_PATH) as con:
                con.execute(
                    """INSERT INTO trades
                    (trade_date, action, ticker, shares, price, asset_type, multiplier, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(source.trade_date), str(source.action), str(source.ticker), float(source.shares),
                        float(source.price), str(source.asset_type), float(source.multiplier),
                        str(source.description or ""),
                    ),
                )
                con.commit()
            st.success("Trade duplicated.")
            st.rerun()

        if col3.button("Delete Trade", use_container_width=True):
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM trades WHERE id=?", (selected_trade_id,))
                con.commit()
            st.success("Trade deleted.")
            st.rerun()

        confirm_clear = st.checkbox("Confirm clear all", key="confirm_clear_all_trades")
        if col4.button("Clear All Trades", use_container_width=True, disabled=not confirm_clear):
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM trades")
                con.commit()
            st.success("All trades cleared.")
            st.rerun()


if active_section == "Backtesting":
    st.subheader("Single-stock dividend-reinvestment backtest")
    b1, b2, b3, b4 = st.columns(4)
    bticker = b1.text_input("Ticker", value=st.session_state.selected_ticker, key="bt_ticker").upper()
    amount = b2.number_input("Initial investment", min_value=1.0, value=1000.0, step=100.0)
    years = int(b3.number_input("Years", min_value=1, max_value=100, value=5, step=1))
    reinvest = b4.checkbox("Reinvest dividends", value=True)
    if bticker:
        st.caption(symbol_company(bticker))
    st.caption(f"Backtest period: {years} year{'s' if years != 1 else ''}")

    if st.button("Run Backtest"):
        try:
            end_date = pd.Timestamp.today().normalize()
            start_date = end_date - pd.DateOffset(years=years)
            hist = yf.Ticker(bticker).history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=False,
                actions=True,
            )
            if hist.empty:
                raise ValueError("No historical data returned for the selected period.")
            hist = hist.dropna(subset=["Close"])
            if hist.empty or float(hist["Close"].iloc[0]) <= 0:
                raise ValueError("No valid closing-price data returned for the selected period.")

            shares_bt = amount / float(hist["Close"].iloc[0])
            cash_div = 0.0
            values = []
            for idx, row in hist.iterrows():
                dividend = sf(row.get("Dividends")) or 0.0
                if dividend:
                    received = shares_bt * dividend
                    if reinvest and row["Close"] > 0:
                        shares_bt += received / row["Close"]
                    else:
                        cash_div += received
                values.append(shares_bt * row["Close"] + cash_div)

            ending = values[-1]
            total_return = (ending / amount - 1) * 100
            elapsed_years = max((hist.index[-1] - hist.index[0]).days / 365.2425, 1 / 365.2425)
            cagr = (ending / amount) ** (1 / elapsed_years) - 1
            m1, m2, m3 = st.columns(3)
            m1.metric("Ending Value", f"${ending:,.2f}")
            m2.metric("Total Return", f"{total_return:,.2f}%")
            m3.metric("CAGR", f"{cagr*100:,.2f}%")
            st.caption(
                f"Data used: {hist.index[0].date():%b %d, %Y} through "
                f"{hist.index[-1].date():%b %d, %Y} ({elapsed_years:.2f} years)."
            )
            fig_bt = go.Figure(go.Scatter(x=hist.index, y=values, name="Portfolio Value"))
            fig_bt.update_layout(title=f"{symbol_company(bticker)} Backtest", height=500, yaxis_title="Value ($)", hovermode="x unified")
            st.plotly_chart(fig_bt, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

if active_section == "Options Finder":
    st.subheader("Options Finder")
    o1, o2, o3, o4, o5 = st.columns(5)
    oticker = o1.text_input("Ticker", key="options_ticker").upper().strip()
    side_label = o2.selectbox("Contracts", ["Puts", "Calls"])
    min_ann = o3.number_input("Min annual return %", value=24.0, step=1.0)
    max_ann = o4.number_input("Max annual return %", value=30.0, step=1.0)
    min_volume = o5.number_input("Minimum volume", value=25, min_value=0, step=1)
    d1, d2, d3 = st.columns(3)
    min_dte = d1.number_input("Min DTE", value=30, min_value=0, step=1)
    max_dte = d2.number_input("Max DTE", value=45, min_value=1, step=1)
    max_delta = d3.number_input("Maximum absolute Delta", value=0.18, min_value=0.01, max_value=1.0, step=0.01)

    action_col, price_col, spacer_col = st.columns([1.1, 1.25, 4.65])
    find_options = action_col.button("Find Options", type="primary", use_container_width=True)

    current_option_price = None
    if oticker:
        st.caption(symbol_company(oticker))
        try:
            current_option_price = quick_quote(oticker)["price"]
        except Exception:
            current_option_price = None
    price_col.metric(
        "Current Stock Price",
        f"${current_option_price:,.2f}" if current_option_price is not None else "—",
    )

    if find_options:
        try:
            spot = current_option_price or valuation(oticker)["Price"]
            expirations = option_expirations(oticker)
            rows = []
            today = date.today()
            side = side_label.lower()
            for exp in expirations:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                dte = (exp_date - today).days
                if dte < min_dte or dte > max_dte:
                    continue
                chain = option_chain(oticker, exp, side)
                for _, r in chain.iterrows():
                    bid, ask = sf(r.get("bid")), sf(r.get("ask"))
                    strike = sf(r.get("strike"))
                    volume = sf(r.get("volume")) or 0
                    iv = sf(r.get("impliedVolatility"))
                    if bid is None or ask is None or strike is None or ask < bid or volume < min_volume:
                        continue
                    mid_price = (bid + ask) / 2
                    if mid_price <= 0:
                        continue
                    delta = option_delta_estimate(spot, strike, dte, iv, side)
                    if delta is not None and abs(delta) > max_delta:
                        continue
                    collateral = strike if side == "puts" else spot
                    ann_return = (mid_price / collateral) * (365 / dte) * 100 if collateral and dte else None
                    if ann_return is None or not (min_ann <= ann_return <= max_ann):
                        continue
                    breakeven = strike - mid_price if side == "puts" else strike + mid_price
                    rows.append({
                        "Ticker": oticker, "Company Name": company_name(oticker),
                        "Expiration": exp, "DTE": dte, "Strike": strike,
                        "Bid": bid, "Ask": ask, "Mid": mid_price, "Delta": delta,
                        "IV %": iv * 100 if iv else None, "Volume": int(volume),
                        "Open Interest": int(sf(r.get("openInterest")) or 0),
                        "Ann. Return %": ann_return, "Break-even": breakeven,
                        "Contract": r.get("contractSymbol"),
                    })
            results = pd.DataFrame(rows).sort_values("Ann. Return %", ascending=False) if rows else pd.DataFrame()
            if results.empty:
                st.warning("No contracts matched the current filters.")
            else:
                st.dataframe(results, use_container_width=True, hide_index=True, column_config={
                    "Strike": st.column_config.NumberColumn(format="$%.2f"), "Bid": st.column_config.NumberColumn(format="$%.2f"),
                    "Ask": st.column_config.NumberColumn(format="$%.2f"), "Mid": st.column_config.NumberColumn(format="$%.2f"),
                    "Delta": st.column_config.NumberColumn(format="%.3f"), "IV %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Ann. Return %": st.column_config.NumberColumn(format="%.2f%%"), "Break-even": st.column_config.NumberColumn(format="$%.2f")
                })
                st.download_button("Download CSV", results.to_csv(index=False), file_name=f"{oticker}_options.csv", mime="text/csv")
        except Exception as exc:
            st.error(f"Options search failed: {exc}")

st.divider()
st.caption("Educational use only. This application does not provide investment advice or place brokerage orders.")
