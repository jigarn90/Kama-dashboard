
import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
import requests

# Telegram credentials
TELEGRAM_TOKEN = '7624558508:AAFCTMKC_VRRkZRfhllPLur8jYUex3kpuu0'
TELEGRAM_CHAT_ID = '1118732238'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Failed to send Telegram message: {e}")

def get_fo_symbols():
    return [
        "ABB.NS", "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ALKEM.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS",
        "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "AUROPHARMA.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS",
        "BAJFINANCE.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS",
        "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS", "BRITANNIA.NS", "BSOFT.NS",
        "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS",
        "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS",
        "DELTACORP.NS", "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS",
        "FEDERALBNK.NS", "FSL.NS", "GAIL.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRASIM.NS",
        "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS", "HCLTECH.NS", "HDFC.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
        "HEROMOTOCO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "HONAUT.NS", "ICICIBANK.NS",
        "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", "IDFCFIRSTB.NS", "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS",
        "INDIAMART.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS", "IPCALAB.NS", "IRCTC.NS",
        "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "LALPATHLAB.NS",
        "LICHSGFIN.NS", "LT.NS", "LTI.NS", "LTTS.NS", "LUPIN.NS", "MANAPPURAM.NS", "MARICO.NS", "MARUTI.NS", "MCDOWELL-N.NS",
        "MCX.NS", "METROPOLIS.NS", "MGL.NS", "MINDTREE.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS",
        "NAM-INDIA.NS", "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS", "NTPC.NS", "OBEROIRLTY.NS",
        "OFSS.NS", "ONGC.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PIDILITIND.NS", "PIIND.NS",
        "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS", "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS", "RELIANCE.NS",
        "SAIL.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SRTRANSFIN.NS",
        "SUNPHARMA.NS", "SUNTV.NS", "SUPREMEIND.NS", "SYMPHONY.NS", "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS",
        "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS",
        "TRENT.NS", "TVSMOTOR.NS", "UBL.NS", "ULTRACEMCO.NS", "UPL.NS", "VBL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS",
        "ZEEL.NS", "ZYDUSLIFE.NS"
    ]

def calculate_kama(df, kama_len=10, fast_ema=2, slow_ema=30):
    direction = abs(df['Close'] - df['Close'].shift(kama_len))
    volatility = sum(abs(df['Close'].shift(i) - df['Close'].shift(i + 1)) for i in range(kama_len))
    er = direction / volatility
    fast_sc = 2 / (fast_ema + 1)
    slow_sc = 2 / (slow_ema + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    kama = [df['Close'].iloc[0]]
    for i in range(1, len(df)):
        kama.append(kama[-1] + sc.iloc[i] * (df['Close'].iloc[i] - kama[-1]))
    df['KAMA'] = kama
    return df

def scan_stock(symbol):
    df = yf.download(symbol, period="5d", interval="15m")
    if df.empty or len(df) < 35:
        return None
    df = calculate_kama(df)
    df['MA'] = df['Close'].rolling(50).mean()
    if df['Close'].iloc[-1] > df['MA'].iloc[-1] and df['Close'].iloc[-2] < df['KAMA'].iloc[-2] and df['Close'].iloc[-1] > df['KAMA'].iloc[-1]:
        return f"📈 BUY Signal for {symbol} | Price: ₹{df['Close'].iloc[-1]:.2f}"
    return None

# Streamlit App
st.set_page_config(page_title="KAMA F&O Scanner", layout="wide")
st.title("📊 NSE F&O KAMA Crossover Scanner")

symbols = get_fo_symbols()
alerts = []

with st.spinner("🔍 Scanning F&O stocks..."):
    for sym in symbols:
        signal = scan_stock(sym)
        if signal:
            alerts.append(signal)
            send_telegram_message(signal)
    st.success("✅ Scan Completed!")

if alerts:
    for msg in alerts:
        st.write(msg)
else:
    st.info("No signals found at the moment.")

# Auto-refresh every 60 seconds
st.experimental_rerun()
