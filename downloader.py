import os
import yaml
import yfinance as yf
import pandas as pd
import time

def cargar_tickers(ruta_yaml="config/tickers.yaml"):
    """Lee el archivo YAML y devuelve un diccionario con las categorías."""
    if not os.path.exists(ruta_yaml) and os.path.exists("tickers.yaml"):
        ruta_yaml = "tickers.yaml"

    if not os.path.exists(ruta_yaml):
        print(f"❌ ERROR: No se encuentra {ruta_yaml}.")
        raise FileNotFoundError(f"No se encuentra el archivo {ruta_yaml}.")

    with open(ruta_yaml, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def descargar_datos(ticker, fecha_inicio="2000-01-01"):
    """Descarga datos históricos diarios para un ticker específico."""
    try:
        # auto_adjust=True es VITAL para corregir dividendos y splits
        df = yf.download(ticker, start=fecha_inicio, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"⚠️ Advertencia: No se encontraron datos para {ticker}.")
            return None
            
        # Aplanar MultiIndex si existe
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        print(f"❌ Error descargando {ticker}: {e}")
        return None

def main():
    # 1. Crear carpeta de datos
    os.makedirs("data", exist_ok=True)
    
    # 2. Cargar configuración
    try:
        universo = cargar_tickers()
    except Exception as e:
        print(f"Fallo al cargar la configuración: {e}")
        return 

    # 3. Extraer TODOS los tickers de TODAS las categorías sin duplicados
    todos_los_tickers = set()
    for categoria, lista_tickers in universo.items():
        if isinstance(lista_tickers, list):
            todos_los_tickers.update(lista_tickers)
            
    # Convertimos a lista y ordenamos alfabéticamente para que sea más limpio
    tickers_a_descargar = sorted(list(todos_los_tickers))
    
    print(f"--- Iniciando descarga del Universo Completo ---")
    print(f"Total de activos únicos a descargar: {len(tickers_a_descargar)}")
    
    # 4. Bucle de descarga
    for i, ticker in enumerate(tickers_a_descargar, 1):
        # Comprobar si ya existe el archivo para no descargarlo dos veces innecesariamente
        nombre_archivo = ticker.replace("^", "").replace("=", "_") + ".csv"
        ruta_guardado = os.path.join("data", nombre_archivo)
        
        if os.path.exists(ruta_guardado):
            print(f"[{i}/{len(tickers_a_descargar)}] ⏩ {ticker} ya existe, saltando...")
            continue

        print(f"[{i}/{len(tickers_a_descargar)}] Descargando {ticker}...")
        df = descargar_datos(ticker)
        
        if df is not None:
            df.to_csv(ruta_guardado)
            print(f"  ✅ Guardado: {ruta_guardado} ({len(df)} filas)")
        
        # Pausa de 0.5 segundos para evitar que Yahoo Finance nos bloquee (Rate Limit)
        time.sleep(0.5)

    print("--- Descarga finalizada ---")

if __name__ == "__main__":
    main()