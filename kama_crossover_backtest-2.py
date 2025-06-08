
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta

# === Telegram Credentials ===
TELEGRAM_TOKEN = '7624558508:AAFCTMKC_VRRkZRfhllPLur8jYUex3kpuu0'
TELEGRAM_CHAT_ID = '1118732238'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=data)

# === KAMA Function ===
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

# === Main Script ===
st.title("📊 KAMA Crossover Backtest with TP/SL & Telegram Alerts")

symbol = st.text_input("Enter Symbol (e.g., BAJFINANCE.NS):", value="BAJFINANCE.NS")
kama_length = st.slider("KAMA Length", 5, 30, 10)
fast_ema = st.slider("Fast EMA", 1, 10, 2)
slow_ema = st.slider("Slow EMA", 20, 50, 30)
ma_length = st.slider("Trend MA Length", 10, 100, 50)
take_profit = st.slider("Take Profit %", 0.5, 5.0, 2.0) / 100
trailing_sl = st.slider("Trailing SL %", 0.5, 3.0, 1.0) / 100

if st.button("Run Strategy"):
    # Download last 2 days of 15-min data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)
    df = yf.download(symbol, start=start_date, end=end_date, interval="15m")
    df.dropna(inplace=True)
    df['MA'] = df['Close'].rolling(ma_length).mean()
    df['KAMA'] = calculate_kama(df['Close'], kama_length, fast_ema, slow_ema)
    df = calculate_adx(df)

    buy_signals = []
    sell_signals = []

    for i in range(1, len(df)):
        trend_up = df['Close'].iloc[i] > df['MA'].iloc[i]
        trend_strong = df['ADX'].iloc[i] > 25
        buy = df['Close'].iloc[i-1] < df['KAMA'].iloc[i-1] and df['Close'].iloc[i] > df['KAMA'].iloc[i] and trend_up and trend_strong
        sell = df['Close'].iloc[i-1] > df['KAMA'].iloc[i-1] and df['Close'].iloc[i] < df['KAMA'].iloc[i] and not trend_up and trend_strong

        if buy:
            buy_signals.append((df.index[i], df['Close'].iloc[i]))
            send_telegram_message(f"📈 BUY @ ₹{df['Close'].iloc[i]:.2f} | TP: ₹{df['Close'].iloc[i] * (1 + take_profit):.2f} | SL Trail: ₹{df['Close'].iloc[i] * (1 - trailing_sl):.2f}")
        elif sell:
            sell_signals.append((df.index[i], df['Close'].iloc[i]))
            send_telegram_message(f"📉 SELL @ ₹{df['Close'].iloc[i]:.2f} | TP: ₹{df['Close'].iloc[i] * (1 - take_profit):.2f} | SL Trail: ₹{df['Close'].iloc[i] * (1 + trailing_sl):.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['KAMA'], name='KAMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA'], name='MA', line=dict(color='blue')))

    for signal in buy_signals:
        fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', marker=dict(color='green', size=10), name='Buy'))
    for signal in sell_signals:
        fig.add_trace(go.Scatter(x=[signal[0]], y=[signal[1]], mode='markers', marker=dict(color='red', size=10), name='Sell'))

    st.plotly_chart(fig, use_container_width=True)
    st.success(f"Strategy executed with {len(buy_signals)} Buy and {len(sell_signals)} Sell signals.")
