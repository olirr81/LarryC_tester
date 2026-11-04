import os
import yfinance as yf
import pandas as pd
import time
import requests

def obtener_tickers_sp500():
    print("Obteniendo lista del S&P 500...")
    
    # 1. Intentar desde Wikipedia con User-Agent de navegador
    url_wiki = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url_wiki, headers=headers, timeout=10)
        response.raise_for_status()
        tables = pd.read_html(response.text)
        df = tables[0]
        tickers = [str(t).replace('.', '-') for t in df['Symbol'].tolist()]
        print(f"✅ Lista obtenida de Wikipedia: {len(tickers)} acciones.")
        return tickers
    except Exception as e:
        print(f"⚠️ Fallo en Wikipedia ({e}). Intentando desde dataset de GitHub...")

    # 2. Plan B: Intentar desde un CSV alojado en GitHub
    url_github = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv'
    try:
        df = pd.read_csv(url_github)
        tickers = [str(t).replace('.', '-') for t in df['Symbol'].tolist()]
        print(f"✅ Lista obtenida de GitHub: {len(tickers)} acciones.")
        return tickers
    except Exception as e:
        print(f"⚠️ Fallo en GitHub ({e}). Usando lista de respaldo (Top 100).")

    # 3. Plan C: Lista de respaldo (Top 100 para que el backtest funcione)
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "XOM",
        "LLY", "JPM", "JNJ", "V", "PG", "MA", "AVGO", "HD", "CVX", "MRK",
        "ABBV", "PEP", "COST", "KO", "ADBE", "WMT", "MCD", "CSCO", "CRM", "TMO",
        "ACN", "ABT", "LIN", "AMD", "DHR", "TXN", "NFLX", "PM", "DIS", "WFC",
        "BMY", "INTC", "VZ", "INTU", "AMGN", "COP", "CAT", "QCOM", "IBM", "GE",
        "RTX", "SPGI", "HON", "UNP", "BA", "LOW", "AMAT", "ELV", "DE", "BKNG",
        "SYK", "GS", "BLK", "ISRG", "MDT", "TJX", "PLD", "GILD", "VRTX", "C",
        "ADP", "MMC", "SBUX", "LMT", "CB", "ADI", "CI", "REGN", "ZTS", "NOW",
        "PGR", "SO", "DUK", "BDX", "ETN", "MU", "BSX", "SLB", "KLAC", "MDLZ",
        "ICE", "CME", "AON", "MCO", "SNPS", "CDNS", "APH", "WM", "EQIX", "NOC"
    ]

def descargar_sp500():
    os.makedirs("data", exist_ok=True)
    tickers = obtener_tickers_sp500()

    for i, ticker in enumerate(tickers, 1):
        nombre_archivo = ticker + ".csv"
        ruta_guardado = os.path.join("data", nombre_archivo)

        # Saltar si ya existe
        if os.path.exists(ruta_guardado):
            continue
        
        try:
            df = yf.download(ticker, start="2000-01-01", progress=False, auto_adjust=True)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df.to_csv(ruta_guardado)
                print(f"[{i}/{len(tickers)}] ✅ {ticker}")
            else:
                print(f"[{i}/{len(tickers)}] ⚠️ {ticker} (sin datos)")
        except Exception as e:
            print(f"[{i}/{len(tickers)}] ❌ {ticker} (error)")
        
        # Pausa para no saturar Yahoo Finance
        time.sleep(0.3)

if __name__ == "__main__":
    descargar_sp500()