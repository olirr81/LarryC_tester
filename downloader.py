import os
import yaml
import yfinance as yf
import pandas as pd
from datetime import datetime

def cargar_tickers(ruta_yaml="config/tickers.yaml"):
    """Lee el archivo YAML y devuelve un diccionario con las categorías."""
    if not os.path.exists(ruta_yaml):
        raise FileNotFoundError(f"No se encuentra el archivo {ruta_yaml}. Verifica la ruta.")
    
    with open(ruta_yaml, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def descargar_datos(ticker, fecha_inicio="2000-01-01"):
    """Descarga datos históricos diarios para un ticker específico."""
    print(f"Descargando {ticker}...")
    try:
        # auto_adjust=True es VITAL para corregir dividendos y splits
        df = yf.download(ticker, start=fecha_inicio, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"⚠️ Advertencia: No se encontraron datos para {ticker}.")
            return None
            
        # Si yfinance devuelve un MultiIndex (común en versiones nuevas), lo aplanamos
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
    universo = cargar_tickers()
    
    # 3. Elegir qué categoría descargar (puedes cambiar esto luego)
    categoria = "original_20" # Empezamos con el universo original de Connors
    tickers_a_descargar = universo.get(categoria, [])
    
    print(f"--- Iniciando descarga de la categoría: {categoria} ---")
    print(f"Total de activos: {len(tickers_a_descargar)}")
    
    # 4. Bucle de descarga
    for ticker in tickers_a_descargar:
        df = descargar_datos(ticker)
        
        if df is not None:
            # Guardar como CSV dentro de la carpeta data/
            # Reemplazamos ^ y = para que los nombres de archivo sean válidos
            nombre_archivo = ticker.replace("^", "").replace("=", "_") + ".csv"
            ruta_guardado = os.path.join("data", nombre_archivo)
            
            df.to_csv(ruta_guardado)
            print(f"✅ Guardado: {ruta_guardado} ({len(df)} filas)")

if __name__ == "__main__":
    main()
