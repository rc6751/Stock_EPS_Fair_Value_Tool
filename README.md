# Stock_EPS_Fair_Value_Tool — Streamlit Edition

## Deploy to Streamlit Community Cloud

1. Extract this ZIP.
2. Upload `app.py`, `requirements.txt`, `.streamlit/config.toml`, and this README to the root of your GitHub repository.
3. In Streamlit Community Cloud, deploy the repository with main file path `app.py`.
4. Do not upload the old Tkinter desktop `app.py`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Yahoo Finance data is unofficial and may be delayed, incomplete, or rate-limited.
- Paper trades use a local SQLite file. Streamlit Community Cloud storage can reset when the app is redeployed or restarted, so use a persistent database for durable multi-user storage.
- The web app includes stock analysis, original and relative fair value, Bollinger Bands, RSI, watchlists, paper trading, a simple dividend-reinvestment backtest, and an options finder.


## Navigation
The main sections are displayed as large side-by-side buttons: Price vs EPS, Watchlists, Paper Trading, Backtesting, and Options Finder.
