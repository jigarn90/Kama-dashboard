
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta

# === Telegram Credentials ===
TELEGRAM_TOKEN = '7624558508:AAFCTMKC_VRRkZRfhllPLur8jYUex3kpuu0'
TELEGRAM_CHAT_ID = '1118732238'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# === F&O Stocks List (updated) ===
fo_stocks = [
    "RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "ITC",
    "HINDUNILVR", "LT", "KOTAKBANK", "MARUTI", "BAJFINANCE", "HCLTECH", "WIPRO",
    "ADANIENT", "TITAN", "POWERGRID", "ONGC", "COALINDIA", "BHARTIARTL", "ULTRACEMCO",
    "SUNPHARMA", "TECHM", "NTPC", "JSWSTEEL", "TATAMOTORS", "DIVISLAB", "HINDALCO",
    "NESTLEIND", "GRASIM", "CIPLA", "DRREDDY", "BAJAJFINSV", "SBILIFE", "BRITANNIA",
    "BPCL", "TATASTEEL", "IOC", "M&M", "HEROMOTOCO", "BAJAJ-AUTO", "EICHERMOT",
    "ASIANPAINT", "SHREECEM", "ADANIPORTS", "HDFCLIFE", "INDUSINDBK", "UPL", "VEDL"
]

# === KAMA Calculation ===
def calculate_kama(df, kama_len=10, fast_ema=2, slow_ema=30):
    close = df['Close']
    direction = abs(close - close.shift(kama_len))
    volatility = close.diff(1).abs().rolling(kama_len).sum()
    er = direction / volatility
    fast_sc = 2 / (fast_ema + 1)
    slow_sc = 2 / (slow_ema + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    kama = [close.iloc[0]]
    for i in range(1, len(close)):
        kama.append(kama[i - 1] + sc.iloc[i] * (close.iloc[i] - kama[i - 1]))
    df['KAMA'] = kama
    df['MA'] = close.rolling(50).mean()
    return df

# === Signal Logic ===
def scan_stock(symbol):
    df = yf.download(f"{symbol}.NS", interval="15m", period="5d", progress=False)
    if df.empty or len(df) < 60:
        return None
    df = calculate_kama(df)
    last_close = df['Close'].iloc[-1].item()
    last_kama = df['KAMA'].iloc[-1].item()
    last_ma = df['MA'].iloc[-1].item()
    prev_close = df['Close'].iloc[-2].item()
    prev_kama = df['KAMA'].iloc[-2].item()

    if (last_close > last_ma) and (prev_close < prev_kama) and (last_close > last_kama):
        return f"📈 BUY Signal for {symbol} | Price: ₹{last_close:.2f}"
    return None

# === Streamlit App ===
st.title("📊 F&O KAMA Crossover Scanner with Telegram Alerts")
results = []
for sym in fo_stocks:
    signal = scan_stock(sym)
    if signal:
        results.append(signal)
        send_telegram_message(signal)

if results:
    for res in results:
        st.success(res)
else:
    st.info("No signals found at this time.")

# Refresh button (manual instead of auto-loop)
if st.button("🔄 Refresh Now"):
    st.experimental_rerun()
