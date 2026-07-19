import math
import sqlite3
import uuid
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

def scroll_page_to_top():
    render_id = uuid.uuid4().hex
    components.html(
        f"""
        <script>
        (() => {{
            const parentWindow = window.parent;
            const parentDocument = parentWindow.document;
            const scrollContainers = [
                parentDocument.documentElement,
                parentDocument.body,
                parentDocument.querySelector('[data-testid="stAppViewContainer"]'),
                parentDocument.querySelector('[data-testid="stMain"]'),
                parentDocument.querySelector('[data-testid="stAppViewBlockContainer"]'),
                parentDocument.querySelector('section.main'),
                parentDocument.querySelector('.main')
            ].filter(Boolean);

            let enabled = true;
            let intervalId;
            let observer;

            const scrollToTop = () => {{
                if (!enabled) return;
                parentWindow.scrollTo({{ top: 0, left: 0, behavior: 'instant' }});
                scrollContainers.forEach(container => {{ container.scrollTop = 0; }});
            }};

            const stopScrolling = () => {{
                enabled = false;
                if (intervalId) parentWindow.clearInterval(intervalId);
                if (observer) observer.disconnect();
            }};

            ['wheel', 'touchmove', 'keydown', 'mousedown'].forEach(eventName => {{
                parentDocument.addEventListener(eventName, stopScrolling, {{ once: true, passive: true }});
            }});

            scrollToTop();

            let attempts = 0;
            intervalId = parentWindow.setInterval(() => {{
                scrollToTop();
                attempts += 1;
                if (attempts > 8) stopScrolling();
            }}, 150);

            observer = new MutationObserver(scrollToTop);
            observer.observe(parentDocument.body, {{ childList: true, subtree: true }});
            parentWindow.setTimeout(stopScrolling, 1200);
        }})();
        </script>
        <!-- render-id: {render_id} -->
        """,
        height=0,
    )


scroll_page_to_top()

render_navigation("home_nav")
        if st.button(f"Analyze {symbol} in Full Dashboard →", type="primary", key="trial_full_analysis"):
            st.session_state.selected_ticker = symbol
            st.session_state.options_ticker = symbol
            st.session_state.active_section = "Price vs EPS"
            st.rerun()
    except Exception as exc:
        st.error(f"Dashboard data unavailable for {symbol}: {exc}")
        render_navigation("home_nav")


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
            metrics = [
                ("Price", v["Price"], "$"), ("Fair Value", v["Original Fair Value"], "$"),
                ("Score", v["Score"], ""), ("Signal", normalize_signal(v["Signal"]), ""),
                ("Dividend Yield", v["Dividend Yield %"], "%"),
            ]
            cols = st.columns(len(metrics))
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
                    "Metric": ["Sector", "Industry", "Trailing EPS", "Forward EPS", "P/E used", "EPS Growth"],
                    "Value": [v["Sector"], v["Industry"], v["Trailing EPS"], v["Forward EPS"], v["P/E"], v["EPS Growth %"]]
                })
                st.dataframe(fundamentals, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not analyze {ticker}: {exc}")
    else:
        st.info("Enter a symbol above, then select Analyze.")

if active_section == "Watchlists":
    st.session_state.setdefault("watchlist_category", "Most Active")
    st.subheader("Watchlists")
    st.markdown("""
    <style>
    .st-key-watchlist_tabs div[data-testid="stButton"] > button {
        min-height: 2.1rem;
        padding: .25rem .4rem;
        font-size: .74rem;
        font-weight: 700;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)
    category_names = ["Most Active", "Top Buys"] + list(CATEGORY_LISTS)
    with st.container(key="watchlist_tabs"):
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
    if category == "Most Active":
        with st.spinner("Loading most actively traded stocks..."):
            tickers = [row["ticker"] for row in most_active_quotes()]
        with st.spinner(f"Loading {category}..."):
            watch_df = scan_group(tuple(tickers))
        st.caption("Ranked by reported trading volume. Click any row to load that ticker directly into the chart and Options Finder.")
    elif category == "Top Buys":
        with st.spinner("Scanning today's most actively traded stocks for BUY signals..."):
            pool_tickers = most_active_symbols(count=100)
            scanned = scan_group(tuple(pool_tickers))
        watch_df = (
            scanned[scanned["Signal"] == "BUY"]
            .sort_values(by="Score", ascending=False, na_position="last")
            .head(10)
            .reset_index(drop=True)
        )
        if watch_df.empty:
            st.info("No BUY-rated stocks found among today's most actively traded tickers right now.")
        else:
            st.caption(
                f"Top {len(watch_df)} BUY-rated stock{'s' if len(watch_df) != 1 else ''} out of "
                f"{len(pool_tickers)} of today's most actively traded tickers scanned. "
                "Click any row to load that ticker directly into the chart and Options Finder."
            )
    else:
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
    if not watch_df.empty:
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
            "Price", "Score", "Original Fair Value", "Signal",
            "P/E", "Forward EPS", "Div.Yield %", "52W Low", "52W High"
        ])
        remaining_columns = [col for col in watch_df.columns if col not in preferred_order]
        watch_df = watch_df[[col for col in preferred_order if col in watch_df.columns] + remaining_columns]
        watch_display_df = watch_df.copy()
        watch_display_df.insert(0, "Name", watch_display_df["Ticker"])
        watch_display_df = watch_display_df.drop(columns=["Ticker", "Company Name"], errors="ignore")

        event = st.dataframe(
            watch_display_df.rename(columns={"Original Fair Value":"Fair Value"}),
            key=f"watchlist_table_{category}",
            use_container_width=False,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Name": st.column_config.TextColumn(width=70),
                "Price": st.column_config.NumberColumn(format="$%.2f", width=80),
                "Score": st.column_config.NumberColumn(width=65),
                "Fair Value": st.column_config.NumberColumn(format="$%.2f", width=95),
                "Signal": st.column_config.TextColumn(width=75),
                "P/E": st.column_config.NumberColumn(format="%.2f", width=65),
                "Forward EPS": st.column_config.NumberColumn(format="%.2f", width=90),
                "% of Total Portfolio": st.column_config.NumberColumn(format="%.2f%%", width=125),
                "Div.Yield %": st.column_config.NumberColumn(format="%.2f%%", width=95),
                "52W Low": st.column_config.NumberColumn(format="$%.2f", width=80),
                "52W High": st.column_config.NumberColumn(format="$%.2f", width=80),
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
