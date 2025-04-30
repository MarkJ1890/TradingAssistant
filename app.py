import streamlit as st
from data import get_data
from strategies import get_highs_lows, detect_recent_candle_pattern, suggest_entry, backtest_strategy
import plotly.graph_objs as go

st.set_page_config(page_title="TradingBot Dashboard", layout="wide")
st.title("🧠 TradingBot - Analyse & Backtest")

tickers = {
    "EUR/USD": "EURUSD=X",
    "Goud": "GC=F",
    "US500": "^GSPC",
    "US100": "^IXIC"
}

ticker_label = st.selectbox("Kies een markt", list(tickers.keys()))
ticker = tickers[ticker_label]

data = get_data(ticker, period='5d', interval='1h')
data_daily = get_data(ticker, period='10d', interval='1d')

if data.empty or data_daily.empty:
    st.error("Geen geldige data beschikbaar.")
else:
    st.subheader("📉 Marktdata & Analyse")
    last_price = round(data['Close'].iloc[-1], 2)
    st.write(f"Laatste prijs: **${last_price}**")

    highs_lows = get_highs_lows(data)
    st.metric("📈 High vandaag", f"${highs_lows['today_high']}")
    st.metric("📉 Low vandaag", f"${highs_lows['today_low']}")
    st.metric("📈 High gisteren", f"${highs_lows['yesterday_high']}")
    st.metric("📉 Low gisteren", f"${highs_lows['yesterday_low']}")

    pattern = detect_recent_candle_pattern(data_daily)
    st.write(f"🕯️ Laatste candlepatroon (1D): `{pattern}`")

    entry = suggest_entry(data, pattern=pattern)
    st.write(f"💡 Voorgestelde positie: **{entry['type']}** rond prijs **${entry['entry']}**")
    st.caption(f"Reden: {entry['reason']}")

    st.subheader("🔁 Backtest op SMA20-strategie")
    bt = backtest_strategy(data)
    st.write(f"Totale rendement: {bt['total_return_%']}%")
    st.write(f"Win ratio: {bt['win_ratio']}%")
    st.write(f"Aantal trades: {bt['num_trades']}")

    st.subheader("📊 Prijsactie")
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candles'
    ))
    fig.update_layout(title="Candlestick chart", height=600)
    st.plotly_chart(fig, use_container_width=True)
