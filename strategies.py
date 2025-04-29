import ta
import pandas as pd
import numpy as np

def get_highs_lows(df):
    yesterday = df.iloc[:-24]
    today = df.iloc[-24:]
    return {
        'yesterday_high': round(yesterday['High'].max(), 2),
        'yesterday_low': round(yesterday['Low'].min(), 2),
        'today_high': round(today['High'].max(), 2),
        'today_low': round(today['Low'].min(), 2),
    }

def detect_recent_candle_pattern(df):
    last = df.iloc[-5:]
    result = []
    for i in range(1, len(last)):
        open_prev = last['Open'].iloc[i-1].item()
        close_prev = last['Close'].iloc[i-1].item()
        open_now = last['Open'].iloc[i].item()
        close_now = last['Close'].iloc[i].item()
        if close_prev < open_prev and close_now > open_now and close_now > close_prev:
            result.append("Bullish Engulfing")
        elif close_prev > open_prev and close_now < open_now and close_now < close_prev:
            result.append("Bearish Engulfing")
    return result[-1] if result else "No clear pattern"

def suggest_entry(df):
    last = df.iloc[-1]
    sma20 = ta.trend.sma_indicator(close=df['Close'], window=20).iloc[-1]
    price = last['Close']
    if price > sma20:
        return {'type': 'LONG', 'entry': round(price, 2)}
    elif price < sma20:
        return {'type': 'SHORT', 'entry': round(price, 2)}
    return {'type': 'HOLD', 'entry': round(price, 2)}

def backtest_strategy(df):
    df = df.copy()
    df['sma'] = ta.trend.sma_indicator(close=df['Close'], window=20)
    df['position'] = 0
    df.loc[df['Close'] > df['sma'], 'position'] = 1
    df.loc[df['Close'] < df['sma'], 'position'] = -1
    df['returns'] = df['Close'].pct_change()
    df['strategy_returns'] = df['returns'] * df['position'].shift(1)
    total_return = df['strategy_returns'].sum()
    return {
        'total_return_%': round(total_return * 100, 2),
        'win_ratio': round((df['strategy_returns'] > 0).mean() * 100, 2),
        'num_trades': int((df['position'].diff() != 0).sum())
    }
