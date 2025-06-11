
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time
from datetime import datetime

# === Telegram Credentials ===
TELEGRAM_TOKEN = '7624558508:AAFCTMKC_VRRkZRfhllPLur8jYUex3kpuu0'
TELEGRAM_CHAT_ID = '1118732238'

# === F&O stock list ===
fo_stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "LT.NS", "SBIN.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "ITC.NS", "HINDUNILVR.NS", "BHARTIARTL.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "COALINDIA.NS", "SUNPHARMA.NS", "POWERGRID.NS", "HCLTECH.NS",
    "TECHM.NS", "TITAN.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "MARUTI.NS", "HEROMOTOCO.NS",
    "M&M.NS", "TATAMOTORS.NS", "ULTRACEMCO.NS", "SHREECEM.NS", "GRASIM.NS", "HINDALCO.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "CIPLA.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "HDFCLIFE.NS", "SBILIFE.NS", "ICICIPRULI.NS",
    "NESTLEIND.NS", "BRITANNIA.NS", "ASIANPAINT.NS", "BERGEPAINT.NS", "PIDILITIND.NS", "DMART.NS"
]

# === KAMA Calculation ===
def calculate_kama(df, kama_len=10, fast_ema=2, slow_ema=30):
    close = df['Close']
    direction = abs(close - close.shift(kama_len))
    volatility = close.diff().abs().rolling(kama_len).sum()
    er = direction / volatility.replace(0, 1)
    fast_sc = 2 / (fast_ema + 1)
    slow_sc = 2 / (slow_ema + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    kama = [close.iloc[0]]
    for i in range(1, len(close)):
        kama.append(kama[-1] + sc.iloc[i] * (close.iloc[i] - kama[-1]))

    df['KAMA'] = kama
    return df

# === Telegram Alert ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# === Scanning Logic ===

def scan_stock(symbol):
    df = yf.download(symbol, period="5d", interval="15m")
    if df.empty or len(df) < 55:
        return None
    df = calculate_kama(df)
    df['MA'] = df['Close'].rolling(50).mean()

    # Ensure all required columns have valid (non-NaN) data
    if df[['Close', 'KAMA', 'MA']].iloc[-1].isnull().any() or df[['Close', 'KAMA']].iloc[-2].isnull().any():
        return None

    last_close = df['Close'].iloc[-1]
    last_kama = df['KAMA'].iloc[-1]
    last_ma = df['MA'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    prev_kama = df['KAMA'].iloc[-2]

    if (last_close > last_ma) and (prev_close < prev_kama) and (last_close > last_kama):
        return f"📈 BUY Signal for {symbol} | Price: ₹{last_close:.2f}"
    return None
# === Streamlit App ===
st.set_page_config(layout="wide")
st.title("📊 KAMA Crossover Signal Scanner (NSE F&O Stocks)")
st.caption("Scans every 1 minute for Buy Signals with Trend Confirmation")

results = []
for sym in fo_stocks:
    signal = scan_stock(sym)
    if signal:
        results.append(signal)
        send_telegram_message(signal)

if results:
    st.success("✅ Signals Found:")
    for res in results:
        st.write(res)
else:
    st.warning("🔍 No Buy Signals at this moment.")

# Auto-refresh every 60 seconds
st.caption(f"⏱️ Last scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
time.sleep(60)
st.experimental_rerun()
