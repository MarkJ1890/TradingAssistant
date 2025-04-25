def generate_signals(df, risk_eur=15, position_size=1):
    if df.empty or len(df) < 60:
        return {
            'signal': 'NO DATA',
            'confidence': 0,
            'sentiment': 'Neutral',
            'pattern': 'N/A',
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

    # Reken stopafstand op basis van €15 risico
    stopafstand = risk_eur / position_size
    if signal == 'LONG':
        sl = price - stopafstand
        tp = price + stopafstand * 2
    elif signal == 'SHORT':
        sl = price + stopafstand
        tp = price - stopafstand * 2
    else:
        sl = tp = None

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
