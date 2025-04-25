import ta
import pandas as pd
import numpy as np

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
    last_closes = df['Close'][-5:]
    if last_closes.is_monotonic_increasing:
        return "Breakout"
    elif last_closes.is_monotonic_decreasing:
        return "Reversal"
    elif abs(last_closes.pct_change().iloc[-1]) < 0.001:
        return "Range"
    return "No pattern"

def generate_signals(df):
    if df.empty or len(df) < 60:
        return {
            'signal': 'NO DATA',
            'confidence': 0,
            'sentiment': 'Neutral',
            'pattern': 'N/A',
            'reasons': ['Onvoldoende data beschikbaar'],
            'entry': None,
            'stoploss': None,
            'takeprofit': None
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

    last = df.iloc[-1]
    confidence = 0
    reasons = []

    rsi = float(last['rsi'])
    macd = float(last['macd'])
    sma_fast = float(last['sma_fast'])
    sma_slow = float(last['sma_slow'])

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

    price = float(last['Close'])
    sl = tp = None
    if signal == 'LONG':
        sl = price * 0.98
        tp = price * 1.03
    elif signal == 'SHORT':
        sl = price * 1.02
        tp = price * 0.97

    pattern = detect_pattern(df)

    return {
        'signal': signal,
        'confidence': confidence,
        'sentiment': sentiment,
        'pattern': pattern,
        'reasons': reasons,
        'entry': round(price, 2),
        'stoploss': round(sl, 2) if sl else None,
        'takeprofit': round(tp, 2) if tp else None,
    }
