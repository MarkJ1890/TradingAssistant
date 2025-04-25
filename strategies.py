import ta
import pandas as pd
import numpy as np
import os

def ensure_series(data, index):
    try:
        if isinstance(data, pd.DataFrame):
            return data.iloc[:, 0]
        elif isinstance(data, np.ndarray) and data.ndim == 2 and data.shape[1] == 1:
            return pd.Series(data[:, 0], index=index)
        elif isinstance(data, pd.Series):
            return data
        return pd.Series(data, index=index)
    except Exception:
        return pd.Series(dtype=float)

def detect_pattern(df):
    last_closes = df['Close'].iloc[-5:]
    if isinstance(last_closes, pd.DataFrame):
        last_closes = last_closes.iloc[:, 0]
    elif isinstance(last_closes, np.ndarray) and last_closes.ndim == 2:
        last_closes = pd.Series(last_closes[:, 0])
    if last_closes.is_monotonic_increasing:
        return "Breakout"
    elif last_closes.is_monotonic_decreasing:
        return "Reversal"
    elif abs(last_closes.pct_change().iloc[-1]) < 0.001:
        return "Range"
    return "No pattern"

def expected_direction(df):
    recent = df['Close'].iloc[-20:]
    trend = recent.pct_change().mean()
    if trend > 0.001:
        return "Uptrend"
    elif trend < -0.001:
        return "Downtrend"
    return "Sideways"

def log_prediction(ticker, signal, direction):
    log_file = "prediction_log.csv"
    entry = pd.DataFrame([{
        "ticker": ticker,
        "signal": signal,
        "expected_direction": direction,
        "timestamp": pd.Timestamp.now()
    }])
    if os.path.exists(log_file):
        entry.to_csv(log_file, mode="a", header=False, index=False)
    else:
        entry.to_csv(log_file, index=False)

def generate_signals(df, ticker="UNKNOWN"):
    if df.empty or len(df) < 60:
        return {
            'signal': 'NO DATA',
            'confidence': 0,
            'sentiment': 'Neutral',
            'pattern': 'N/A',
            'expected_direction': 'N/A',
            'reasons': ['Onvoldoende data beschikbaar'],
            'entry': None,
            'stoploss': None,
            'takeprofit': None,
        }

    df = df.copy()
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    elif isinstance(close, np.ndarray) and close.ndim == 2 and close.shape[1] == 1:
        close = pd.Series(close[:, 0], index=df.index)

    df['rsi'] = ensure_series(ta.momentum.RSIIndicator(close=close).rsi(), df.index)
    df['macd'] = ensure_series(ta.trend.MACD(close=close).macd_diff(), df.index)
    df['sma_fast'] = ensure_series(ta.trend.sma_indicator(close=close, window=20), df.index)
    df['sma_slow'] = ensure_series(ta.trend.sma_indicator(close=close, window=50), df.index)

    last = df.iloc[[-1]]
    rsi = last['rsi'].iloc[0]
    macd = last['macd'].iloc[0]
    sma_fast = last['sma_fast'].iloc[0]
    sma_slow = last['sma_slow'].iloc[0]
    price = last['Close'].iloc[0]

    confidence = 0
    reasons = []
    sentiment = "Neutral"
    if sma_fast > sma_slow and macd > 0:
        sentiment = "Bullish"
    elif sma_fast < sma_slow and macd < 0:
        sentiment = "Bearish"

    if rsi < 30:
        signal = 'LONG'
        confidence += 30
        reasons.append("RSI < 30 (oversold)")
    elif rsi > 70:
        signal = 'SHORT'
        confidence += 30
        reasons.append("RSI > 70 (overbought)")
    else:
        signal = 'HOLD'

    if macd > 0 and signal == 'LONG':
        confidence += 20
        reasons.append("MACD bullish")
    elif macd < 0 and signal == 'SHORT':
        confidence += 20
        reasons.append("MACD bearish")

    if sma_fast > sma_slow and signal == 'LONG':
        confidence += 20
        reasons.append("SMA 20 > SMA 50")
    elif sma_fast < sma_slow and signal == 'SHORT':
        confidence += 20
        reasons.append("SMA 20 < SMA 50")

    pattern = detect_pattern(df)
    direction = expected_direction(df)

    log_prediction(ticker, signal, direction)

    return {
        'signal': signal,
        'confidence': confidence,
        'sentiment': sentiment,
        'pattern': pattern,
        'expected_direction': direction,
        'reasons': reasons,
        'entry': round(price, 2),
        'stoploss': None,
        'takeprofit': None,
    }
