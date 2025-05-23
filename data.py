import yfinance as yf
import pandas as pd

def get_data(ticker: str, period='5d', interval='1h'):
    try:
        df = yf.download(ticker, period=period, interval=interval)
        return df
    except Exception as e:
        print(f"Fout bij ophalen van data: {e}")
        return pd.DataFrame()
