import os
import yfinance as yf
import pandas as pd
import time

def obtener_tickers_sp500():
    print("Obteniendo lista del S&P 500 desde Wikipedia...")
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    # pandas lee las tablas de la web directamente
    tables = pd.read_html(url)
    df = tables[0]
    # Limpiamos los tickers (ej. BRK.B -> BRK-B para Yahoo Finance)
    tickers = [str(t).replace('.', '-') for t in df['Symbol'].tolist()]
    return tickers

def descargar_sp500():
    os.makedirs("data", exist_ok=True)
    tickers = obtener_tickers_sp500()
    print(f"Total acciones encontradas: {len(tickers)}")

    for i, ticker in enumerate(tickers, 1):
        nombre_archivo = ticker + ".csv"
        ruta_guardado = os.path.join("data", nombre_archivo)

        # Si ya lo descargamos antes, lo saltamos (para ahorrar tiempo si falla a medias)
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
        
        # Pausa de 0.3 segundos para evitar el bloqueo de Yahoo Finance
        time.sleep(0.3)

if __name__ == "__main__":
    descargar_sp500()
