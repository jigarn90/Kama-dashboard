
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta
from nsepy.derivatives import get_expiry_date

# === Telegram Credentials ===
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=data)

# === KAMA Calculation ===
def calculate_kama(series, length, fast_ema, slow_ema):
    direction = abs(series - series.shift(length))
    volatility = sum([abs(series.shift(i) - series.shift(i+1)) for i in range(length)])
    er = direction / volatility
    fast_sc = 2 / (fast_ema + 1)
    slow_sc = 2 / (slow_ema + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    kama = [series.iloc[0]]
    for i in range(1, len(series)):
        kama.append(kama[i-1] + sc.iloc[i] * (series.iloc[i] - kama[i-1]))
    return pd.Series(kama, index=series.index)

# === ADX Calculation ===
def calculate_adx(df):
    df['TR'] = df[['High', 'Low', 'Close']].max(axis=1) - df[['High', 'Low', 'Close']].min(axis=1)
    df['+DM'] = df['High'].diff()
    df['-DM'] = -df['Low'].diff()
    df['+DM'] = df['+DM'].where((df['+DM'] > df['-DM']) & (df['+DM'] > 0), 0.0)
    df['-DM'] = df['-DM'].where((df['-DM'] > df['+DM']) & (df['-DM'] > 0), 0.0)
    df['TR14'] = df['TR'].rolling(14).sum()
    df['+DI'] = 100 * df['+DM'].rolling(14).sum() / df['TR14']
    df['-DI'] = 100 * df['-DM'].rolling(14).sum() / df['TR14']
    df['DX'] = (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])) * 100
    df['ADX'] = df['DX'].rolling(14).mean()
    return df

# === Load Full F&O Stock List ===
def load_fno_list():
    url = "https://www1.nseindia.com/content/fo/fo_mktlots.csv"
    df = pd.read_csv(url)
    return sorted(list(set(df['SYMBOL'].dropna().astype(str))))

fno_stock_symbols = load_fno_list()
fno_stocks = [symbol + ".NS" for symbol in fno_stock_symbols]

# === Streamlit UI ===
st.set_page_config(page_title="KAMA F&O Dashboard", layout="wide")
st.title("📈 F&O Cash Stocks - 15 Min KAMA Crossover Scanner")

kama_length = st.slider("KAMA Length", 5, 30, 10)
fast_ema = st.slider("Fast EMA", 1, 10, 2)
slow_ema = st.slider("Slow EMA", 20, 50, 30)
ma_length = st.slider("Trend MA Length", 10, 100, 50)
take_profit = st.slider("Take Profit %", 0.5, 5.0, 2.0) / 100
trailing_sl = st.slider("Trailing SL %", 0.5, 3.0, 1.0) / 100

if st.button("Run Scanner"):
    signals = []
    for symbol in fno_stocks:
        try:
            df = yf.download(symbol, period="10d", interval="15m")
            df.dropna(inplace=True)
            df['MA'] = df['Close'].rolling(ma_length).mean()
            df['KAMA'] = calculate_kama(df['Close'], kama_length, fast_ema, slow_ema)
            df = calculate_adx(df)

            for i in range(1, len(df)):
                trend_up = df['Close'].iloc[i] > df['MA'].iloc[i]
                trend_strong = df['ADX'].iloc[i] > 25
                buy = df['Close'].iloc[i-1] < df['KAMA'].iloc[i-1] and df['Close'].iloc[i] > df['KAMA'].iloc[i] and trend_up and trend_strong
                sell = df['Close'].iloc[i-1] > df['KAMA'].iloc[i-1] and df['Close'].iloc[i] < df['KAMA'].iloc[i] and not trend_up and trend_strong

                price = df['Close'].iloc[i]
                if buy:
                    tp = price * (1 + take_profit)
                    sl = price * (1 - trailing_sl)
                    msg = f"📍 BUY Signal: {symbol}
Price: ₹{price:.2f}
TP: ₹{tp:.2f}
SL: ₹{sl:.2f}"
                    send_telegram_message(msg)
                    signals.append(msg)
                elif sell:
                    tp = price * (1 - take_profit)
                    sl = price * (1 + trailing_sl)
                    msg = f"📍 SELL Signal: {symbol}
Price: ₹{price:.2f}
TP: ₹{tp:.2f}
SL: ₹{sl:.2f}"
                    send_telegram_message(msg)
                    signals.append(msg)
        except:
            continue

    if signals:
        st.success(f"{len(signals)} signals generated and sent to Telegram.")
        for s in signals:
            st.code(s)
    else:
        st.warning("No signals generated.")
