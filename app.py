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
import yfinance as yf

st.set_page_config(page_title="Stock_EPS_Fair_Value_Tool", page_icon="📈", layout="wide")

st.markdown("""
<style>
:root { --ink:#0a1630; --blue:#2563eb; --cyan:#22d3ee; --panel:#101d3d; }
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100%;}
div[data-testid="stHorizontalBlock"] > div {min-width: 0;}
div.stButton > button {
    min-height: 3.15rem; font-size: 1rem; font-weight: 750; border-radius: 10px;
}
[data-testid="stSidebar"] {min-width: 285px; max-width: 285px;}
.nav-label {font-size: .82rem; color: #777; margin-bottom: .15rem;}
.brandbar {display:flex;align-items:center;justify-content:space-between;padding:.35rem .2rem .8rem;}
.brandname {font-weight:850;font-size:1.15rem;letter-spacing:-.02em;}
.brandtag {font-size:.78rem;opacity:.7;}
.hero {
  position:relative; overflow:hidden; min-height:520px; border-radius:24px; padding:64px 62px;
  background:linear-gradient(135deg,#071226 0%,#102451 52%,#0a3a5e 100%);
  color:white; box-shadow:0 24px 70px rgba(4,18,48,.22); margin:8px 0 28px;
}
.hero:before {content:"";position:absolute;width:480px;height:480px;border-radius:50%;right:-120px;top:-190px;background:radial-gradient(circle,rgba(34,211,238,.35),rgba(37,99,235,0));}
.hero:after {content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to right,transparent 0%,black 55%);}
.hero-copy {position:relative;z-index:2;max-width:720px;padding-top:8px;padding-right:250px;}
.eyebrow {display:inline-block;padding:7px 12px;border:1px solid rgba(255,255,255,.22);border-radius:999px;background:rgba(255,255,255,.08);font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}
.hero h1 {font-size:4rem;line-height:1.02;letter-spacing:-.055em;margin:22px 0 18px;max-width:740px;}
.hero p {font-size:1.15rem;line-height:1.65;color:rgba(255,255,255,.78);max-width:600px;}
.market-card {position:absolute;z-index:3;right:24px;top:24px;width:255px;padding:15px;border:1px solid rgba(255,255,255,.16);border-radius:20px;background:rgba(7,18,38,.68);backdrop-filter:blur(15px);box-shadow:0 24px 70px rgba(0,0,0,.3);}
.market-card .ticker {display:flex;justify-content:space-between;align-items:end;margin-bottom:12px;}
.market-card .price {font-size:1.45rem;font-weight:850;}
.market-card .gain {color:#5ee8a5;font-weight:750;}
.spark {width:100%;height:105px;}
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
    "Top 50": [
        "NVDA","TSLA","AAPL","AMD","AMZN","SOFI","PLTR","INTC","F","BAC",
        "MU","NIO","MARA","RIVN","LCID","T","PFE","CCL","AAL","SNAP",
        "MSFT","META","GOOGL","NFLX","AVGO","QCOM","CSCO","ORCL","CRM","UBER",
        "SHOP","COIN","HOOD","PYPL","XYZ","JPM","WFC","C","XOM","CVX",
        "KO","WMT","DIS","BA","GM","DAL","RBLX","DKNG","RIOT","SOUN"
    ],
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
        "AAPL","AXP","KO","BAC","CVX","OXY","MCO","CB","KHC","DVA",
        "VRSN","SIRI","AMZN","DPZ","POOL","NUE","HEI","CHTR","LEN","LPX"
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
            price REAL NOT NULL
        )""")
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
    signal = "STRONG BUY" if score >= 80 else "BUY" if score >= 65 else "HOLD" if score >= 45 else "SELL"

    return {
        "Ticker": ticker, "Price": current, "Original Fair Value": original,
        "Relative Fair Value": relative, "Score": score, "Signal": signal,
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
                "Ticker", "Price", "Original Fair Value", "Relative Fair Value", "Score", "Signal",
                "P/E", "Forward EPS", "Annual Dividend", "Dividend Yield %", "52W Low", "52W High"
            ]})
        except Exception:
            rows.append({"Ticker": ticker, "Signal": "DATA ERROR"})
    return pd.DataFrame(rows)


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

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.04)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=upper, name="BB Upper", line=dict(width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=mid, name="BB Mid", line=dict(width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=lower, name="BB Lower", line=dict(width=1), fill="tonexty", fillcolor="rgba(128,128,128,0.10)"), row=1, col=1)

    for label, value, dash in [
        ("Original FV", v.get("Original Fair Value"), "dash"),
        ("Relative FV", v.get("Relative Fair Value"), "dot"),
    ]:
        if value:
            fig.add_hline(y=value, line_dash=dash, annotation_text=f"{label} ${value:,.2f}", annotation_position="right", row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI 14", line=dict(width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", row=2, col=1)
    fig.add_hline(y=50, line_dash="dot", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", row=2, col=1)
    latest_rsi = sf(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else None
    if latest_rsi is not None:
        fig.add_annotation(x=df.index[-1], y=latest_rsi, text=f"RSI {latest_rsi:.1f}", showarrow=True, row=2, col=1)

    values = pd.concat([close.loc[df.index], upper, lower]).dropna()
    extras = [x for x in (v.get("Original Fair Value"), v.get("Relative Fair Value")) if x]
    if not values.empty:
        ymin = min([values.min()] + extras)
        ymax = max([values.max()] + extras)
        pad = max((ymax - ymin) * 0.08, ymax * 0.01)
        fig.update_yaxes(range=[ymin-pad, ymax+pad], side="right", row=1, col=1)
    fig.update_yaxes(range=[0, 100], side="right", row=2, col=1)
    fig.update_layout(
        title=f"{ticker} — Price, Bollinger Bands, Fair Values and RSI",
        height=760, xaxis_rangeslider_visible=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=110, t=85, b=20),
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
        ticker = str(r.ticker).upper()
        shares, price = float(r.shares), float(r.price)
        if r.action == "BUY":
            cash -= shares * price
            pos = positions.setdefault(ticker, {"shares": 0.0, "cost": 0.0})
            pos["shares"] += shares
            pos["cost"] += shares * price
        else:
            pos = positions.setdefault(ticker, {"shares": 0.0, "cost": 0.0})
            avg = pos["cost"] / pos["shares"] if pos["shares"] else 0
            sold = min(shares, pos["shares"])
            realized += sold * (price - avg)
            pos["shares"] -= sold
            pos["cost"] -= sold * avg
            cash += shares * price
    rows, market_value, unrealized = [], 0.0, 0.0
    for ticker, pos in positions.items():
        if pos["shares"] <= 1e-9:
            continue
        try:
            price = valuation(ticker)["Price"] or 0
        except Exception:
            price = 0
        avg = pos["cost"] / pos["shares"]
        mv = pos["shares"] * price
        pnl = pos["shares"] * (price - avg)
        market_value += mv
        unrealized += pnl
        rows.append({"Ticker": ticker, "Shares": pos["shares"], "Avg Cost": avg, "Current Price": price, "Market Value": mv, "Unrealized P&L": pnl})
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
    return {
        "ticker": ticker, "name": info.get("shortName") or info.get("longName") or ticker,
        "price": price, "change": change, "change_pct": change_pct,
        "volume": sf(info.get("volume")) or sf(info.get("regularMarketVolume")),
        "market_cap": sf(info.get("marketCap")), "pe": sf(info.get("trailingPE")),
        "eps": sf(info.get("trailingEps")), "dividend_yield": (sf(info.get("dividendYield")) or 0) * 100,
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

def render_homepage():
    st.markdown("""
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">Live markets + smarter valuation</span>
        <h1>Markets at a glance. Fair value in one click.</h1>
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

    launch_left, launch_mid, launch_right = st.columns([1.2, 1, 4])
    with launch_left:
        if st.button("Launch Dashboard  →", type="primary", use_container_width=True, key="hero_launch"):
            st.session_state.active_section = "Price vs EPS"
            st.rerun()
    with launch_mid:
        if st.button("Explore Watchlists", use_container_width=True, key="hero_watchlists"):
            st.session_state.active_section = "Watchlists"
            st.rerun()

    st.markdown('<div class="section-title">Instant market quote</div><div class="section-copy">Enter a stock symbol for a Yahoo Finance-style snapshot, then open the complete analysis.</div>', unsafe_allow_html=True)
    q1, q2 = st.columns([5,1])
    with q1:
        home_ticker = st.text_input("Stock symbol", value=st.session_state.get("home_quote_ticker", "AAPL"), label_visibility="collapsed", placeholder="Enter ticker — AAPL, MSFT, KO...").upper().strip()
    with q2:
        get_quote = st.button("Get Quote", type="primary", use_container_width=True, key="home_get_quote")
    if get_quote and home_ticker:
        st.session_state.home_quote_ticker = home_ticker
    quote_ticker = st.session_state.get("home_quote_ticker", "AAPL")
    try:
        q = quick_quote(quote_ticker)
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        delta = None if q["change"] is None else f'{q["change"]:+.2f} ({q["change_pct"]:+.2f}%)'
        c1.metric(q["ticker"], money(q["price"]), delta)
        c2.metric("Volume", compact_number(q["volume"]))
        c3.metric("Market Cap", compact_number(q["market_cap"]))
        c4.metric("P/E", "N/A" if q["pe"] is None else f'{q["pe"]:.2f}')
        c5.metric("EPS", "N/A" if q["eps"] is None else f'${q["eps"]:.2f}')
        c6.metric("Dividend Yield", f'{q["dividend_yield"]:.2f}%')
        if st.button(f'Analyze {q["ticker"]} in Full Dashboard →', type="primary", key="home_analyze_quote"):
            st.session_state.selected_ticker = q["ticker"]
            st.session_state.options_ticker = q["ticker"]
            st.session_state.active_section = "Price vs EPS"
            st.rerun()
    except Exception as exc:
        st.warning(f"Quote unavailable for {quote_ticker}: {exc}")

    st.markdown('<div class="section-title">Major markets</div><div class="section-copy">Click any market to load its quote above.</div>', unsafe_allow_html=True)
    market_assets = [("S&P 500","^GSPC"),("Nasdaq","^IXIC"),("Dow","^DJI"),("Bitcoin","BTC-USD"),("WTI Oil","CL=F")]
    market_cols = st.columns(5)
    for col, (label, symbol) in zip(market_cols, market_assets):
        with col:
            try:
                mq = quick_quote(symbol)
                delta = "" if mq["change_pct"] is None else f'{mq["change_pct"]:+.2f}%'
                st.metric(label, money(mq["price"]), delta)
            except Exception:
                st.metric(label, "Unavailable")
            if st.button("View", key=f"market_{symbol}", use_container_width=True):
                st.session_state.home_quote_ticker = symbol
                st.rerun()

    st.markdown('<div class="section-title">Top 10 most actively traded</div><div class="section-copy">Ranked by reported trading volume. Click a symbol to update the instant quote.</div>', unsafe_allow_html=True)
    try:
        active = most_active_quotes()
        for rank, row in enumerate(active, 1):
            a,b,c,d,e = st.columns([.5,1.2,3,1.4,1.2])
            a.write(f"**{rank}**")
            if b.button(row["ticker"], key=f"active_{rank}_{row['ticker']}", use_container_width=True):
                st.session_state.home_quote_ticker = row["ticker"]
                st.rerun()
            c.write(row["name"])
            d.write(money(row["price"]))
            pct = row.get("change_pct")
            e.write("N/A" if pct is None else f"{pct:+.2f}%")
    except Exception as exc:
        st.info(f"Most-active data is temporarily unavailable: {exc}")

    st.markdown("""
    <div class="feature-grid">
      <div class="feature-card"><div class="feature-icon">📈</div><h3>Price vs. EPS</h3><p>Compare market price with earnings-driven fair value on an interactive chart.</p></div>
      <div class="feature-card"><div class="feature-icon">👑</div><h3>Curated Watchlists</h3><p>Load Dividend Kings and other focused lists into the chart with one click.</p></div>
      <div class="feature-card"><div class="feature-icon">🎯</div><h3>Options Finder</h3><p>Filter contracts by return, expiration, estimated delta and volume.</p></div>
    </div>
    <div class="site-footer"><b>Stock EPS Fair Value Tool</b><br>For educational and informational purposes only. Quotes may be delayed, incomplete or inaccurate. Nothing presented is investment advice or a recommendation to buy or sell any security.</div>
    """, unsafe_allow_html=True)

init_db()
for key, value in {
    "selected_ticker": "AAPL", "options_ticker": "AAPL", "manual_growth": "", "manual_pe": ""
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

st.markdown('<div class="brandbar"><div><div class="brandname">Stock EPS Fair Value Tool</div><div class="brandtag">Research • Valuation • Technicals</div></div><div class="brandtag">Market intelligence, simplified</div></div>', unsafe_allow_html=True)

section_names = [
    ("⌂", "Home"),
    ("📈", "Price vs EPS"),
    ("📋", "Watchlists"),
    ("💼", "Paper Trading"),
    ("🧪", "Backtesting"),
    ("🔎", "Options Finder"),
]
nav_columns = st.columns(len(section_names), gap="small")
for nav_col, (icon, section_name) in zip(nav_columns, section_names):
    with nav_col:
        if st.button(
            f"{icon}  {section_name}",
            key=f"nav_{section_name}",
            use_container_width=True,
            type="primary" if st.session_state.active_section == section_name else "secondary",
        ):
            st.session_state.active_section = section_name
            st.rerun()

active_section = st.session_state.active_section

ticker = st.session_state.selected_ticker.upper().strip()
history_months = 3
mg_text = st.session_state.manual_growth
pe_text = st.session_state.manual_pe

if active_section == "Home":
    render_homepage()
else:
    st.caption("Yahoo Finance data is unofficial and may be delayed or rate-limited.")
    with st.sidebar:
        st.header("Stock analysis")
        ticker = st.text_input("Ticker", key="selected_ticker").upper().strip()
        history_months = st.radio("Chart history", [1, 3, 6], index=1, horizontal=True, format_func=lambda x: f"{x}M")
        mg_text = st.text_input("Manual EPS growth %", key="manual_growth")
        pe_text = st.text_input("Manual fair P/E", key="manual_pe")
        st.button("Analyze", type="primary", use_container_width=True)
        if st.button("Clear data cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cached Yahoo data cleared.")
    st.divider()

if active_section == "Price vs EPS":
    if ticker:
        try:
            mg = float(mg_text) if mg_text.strip() else None
            mpe = float(pe_text) if pe_text.strip() else None
            with st.spinner(f"Loading {ticker}..."):
                v = valuation(ticker, mg, mpe)
            cols = st.columns(6)
            metrics = [
                ("Price", v["Price"], "$"), ("Original FV", v["Original Fair Value"], "$"),
                ("Relative FV", v["Relative Fair Value"], "$"), ("Score", v["Score"], ""),
                ("Signal", v["Signal"], ""), ("Dividend Yield", v["Dividend Yield %"], "%"),
            ]
            for c, (label, value, unit) in zip(cols, metrics):
                if isinstance(value, (int, float)) and value is not None:
                    text = f"${value:,.2f}" if unit == "$" else f"{value:,.2f}%" if unit == "%" else f"{value}"
                else:
                    text = value or "N/A"
                c.metric(label, text)
            st.plotly_chart(chart_figure(ticker, v, history_months), use_container_width=True, config={"displaylogo": False})
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
        st.info("Enter a ticker in the sidebar.")

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
    st.caption("Click any row to load that ticker directly into the chart and Options Finder.")
    event = st.dataframe(
        watch_df,
        key=f"watchlist_table_{category}",
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "Original Fair Value": st.column_config.NumberColumn(format="$%.2f"),
            "Relative Fair Value": st.column_config.NumberColumn(format="$%.2f"),
            "P/E": st.column_config.NumberColumn(format="%.2f"),
            "Forward EPS": st.column_config.NumberColumn(format="%.2f"),
            "Annual Dividend": st.column_config.NumberColumn(format="$%.2f"),
            "Dividend Yield %": st.column_config.NumberColumn(format="%.2f%%"),
            "52W Low": st.column_config.NumberColumn(format="$%.2f"),
            "52W High": st.column_config.NumberColumn(format="$%.2f"),
        }
    )
    selected_rows = event.selection.rows if event and hasattr(event, "selection") else []
    if selected_rows:
        selected = str(watch_df.iloc[selected_rows[0]]["Ticker"]).upper().strip()
        st.session_state.pending_watchlist_ticker = selected
        st.rerun()

if active_section == "Paper Trading":
    trades = load_trades()
    cash, mv, account, realized, unrealized, positions = portfolio_summary(trades)
    a, b, c, d, e = st.columns(5)
    a.metric("Cash", f"${cash:,.2f}")
    b.metric("Positions", f"${mv:,.2f}")
    c.metric("Account Value", f"${account:,.2f}")
    d.metric("Unrealized P&L", f"${unrealized:,.2f}")
    e.metric("Realized P&L", f"${realized:,.2f}")

    with st.expander("Paper trade entry", expanded=True):
        p1, p2, p3, p4, p5 = st.columns(5)
        pticker = p1.text_input("Ticker", value=st.session_state.selected_ticker, key="paper_ticker").upper()
        action = p2.selectbox("Action", ["BUY", "SELL"])
        shares = p3.number_input("Shares", min_value=0.01, value=100.0, step=1.0)
        default_price = 0.0
        try:
            default_price = valuation(pticker)["Price"] or 0.0
        except Exception:
            pass
        price = p4.number_input("Price", min_value=0.0, value=float(default_price), step=0.01)
        trade_date = p5.date_input("Date", value=date.today())
        if st.button("Save Paper Trade", type="primary"):
            with sqlite3.connect(DB_PATH) as con:
                con.execute("INSERT INTO trades(trade_date,action,ticker,shares,price) VALUES(?,?,?,?,?)",
                            (trade_date.isoformat(), action, pticker, shares, price))
                con.commit()
            st.success("Paper trade saved.")
            st.rerun()

    if not positions.empty:
        st.subheader("Open positions")
        st.dataframe(positions, use_container_width=True, hide_index=True, column_config={
            "Avg Cost": st.column_config.NumberColumn(format="$%.2f"), "Current Price": st.column_config.NumberColumn(format="$%.2f"),
            "Market Value": st.column_config.NumberColumn(format="$%.2f"), "Unrealized P&L": st.column_config.NumberColumn(format="$%.2f")
        })
    st.subheader("Trade history")
    if trades.empty:
        st.info("No paper trades yet.")
    else:
        edited = st.data_editor(trades, use_container_width=True, hide_index=True, disabled=["id"], num_rows="fixed", key="trade_editor")
        col1, col2, col3 = st.columns([1, 1, 2])
        if col1.button("Save edited trades"):
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM trades")
                for _, r in edited.iterrows():
                    con.execute("INSERT INTO trades(id,trade_date,action,ticker,shares,price) VALUES(?,?,?,?,?,?)",
                                (int(r.id), str(r.trade_date), str(r.action), str(r.ticker).upper(), float(r.shares), float(r.price)))
                con.commit()
            st.success("Trades updated.")
            st.rerun()
        delete_id = col2.number_input("Trade ID to delete", min_value=0, step=1, value=0)
        if col3.button("Delete trade") and delete_id:
            with sqlite3.connect(DB_PATH) as con:
                con.execute("DELETE FROM trades WHERE id=?", (int(delete_id),))
                con.commit()
            st.rerun()
    new_cash = st.number_input("Starting cash", min_value=0.0, value=float(starting_cash()), step=1000.0)
    if st.button("Save starting cash"):
        save_starting_cash(new_cash)
        st.success("Starting cash saved.")

if active_section == "Backtesting":
    st.subheader("Single-stock dividend-reinvestment backtest")
    b1, b2, b3, b4 = st.columns(4)
    bticker = b1.text_input("Ticker", value=st.session_state.selected_ticker, key="bt_ticker").upper()
    amount = b2.number_input("Initial investment", min_value=1.0, value=1000.0, step=100.0)
    years = b3.selectbox("Years", [1, 3, 5, 10], index=2)
    reinvest = b4.checkbox("Reinvest dividends", value=True)
    if st.button("Run Backtest"):
        try:
            hist = yf.Ticker(bticker).history(period=f"{years}y", auto_adjust=False, actions=True)
            if hist.empty:
                raise ValueError("No historical data returned.")
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
            cagr = (ending / amount) ** (1 / years) - 1
            m1, m2, m3 = st.columns(3)
            m1.metric("Ending Value", f"${ending:,.2f}")
            m2.metric("Total Return", f"{total_return:,.2f}%")
            m3.metric("CAGR", f"{cagr*100:,.2f}%")
            fig_bt = go.Figure(go.Scatter(x=hist.index, y=values, name="Portfolio Value"))
            fig_bt.update_layout(height=500, yaxis_title="Value ($)", hovermode="x unified")
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

    if st.button("Find Options", type="primary"):
        try:
            spot = valuation(oticker)["Price"]
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
                        "Expiration": exp, "DTE": dte, "Strike": strike,
                        "Bid": bid, "Ask": ask, "Mid": mid_price, "Delta": delta,
                        "IV %": iv * 100 if iv else None, "Volume": int(volume),
                        "Open Interest": int(sf(r.get("openInterest")) or 0),
                        "Annualized Return %": ann_return, "Break-even": breakeven,
                        "Contract": r.get("contractSymbol"),
                    })
            results = pd.DataFrame(rows).sort_values("Annualized Return %", ascending=False) if rows else pd.DataFrame()
            if results.empty:
                st.warning("No contracts matched the current filters.")
            else:
                st.dataframe(results, use_container_width=True, hide_index=True, column_config={
                    "Strike": st.column_config.NumberColumn(format="$%.2f"), "Bid": st.column_config.NumberColumn(format="$%.2f"),
                    "Ask": st.column_config.NumberColumn(format="$%.2f"), "Mid": st.column_config.NumberColumn(format="$%.2f"),
                    "Delta": st.column_config.NumberColumn(format="%.3f"), "IV %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Annualized Return %": st.column_config.NumberColumn(format="%.2f%%"), "Break-even": st.column_config.NumberColumn(format="$%.2f")
                })
                st.download_button("Download CSV", results.to_csv(index=False), file_name=f"{oticker}_options.csv", mime="text/csv")
        except Exception as exc:
            st.error(f"Options search failed: {exc}")

st.divider()
st.caption("Educational use only. This application does not provide investment advice or place brokerage orders.")
