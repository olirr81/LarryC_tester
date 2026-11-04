import os
import yaml
import yfinance as yf
import pandas as pd
from datetime import datetime

def cargar_tickers(ruta_yaml="config/tickers.yaml"):
    """Lee el archivo YAML y devuelve un diccionario con las categorías."""
    # Red de seguridad: si no está en config/, buscar en la raíz
    if not os.path.exists(ruta_yaml) and os.path.exists("tickers.yaml"):
        print("⚠️ No se encontró 'config/tickers.yaml'. Usando 'tickers.yaml' de la raíz.")
        ruta_yaml = "tickers.yaml"

    if not os.path.exists(ruta_yaml):
        print("❌ ERROR CRÍTICO: No se encuentra el archivo de tickers.")
        print(f"Archivos en la raíz del repo: {os.listdir('.')}")
        if os.path.exists("config"):
            print(f"Archivos DENTRO de config: {os.listdir('config')}")
        raise FileNotFoundError(f"No se encuentra el archivo {ruta_yaml}.")

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
    try:
        universo = cargar_tickers()
    except Exception as e:
        print(f"Fallo al cargar la configuración: {e}")
        return # Detenemos el script si no hay tickers

    # 3. Elegir qué categoría descargar (puedes cambiar "original_20" por otra)
    categoria = "original_20" 
    tickers_a_descargar = universo.get(categoria, [])
    
    print(f"--- Iniciando descarga de la categoría: {categoria} ---")
    print(f"Total de activos: {len(tickers_a_descargar)}")
    
    # 4. Bucle de descarga
    for ticker in tickers_a_descargar:
        df = descargar_datos(ticker)
        
        if df is not None:
            # Guardar como CSV dentro de la carpeta data/
            nombre_archivo = ticker.replace("^", "").replace("=", "_") + ".csv"
            ruta_guardado = os.path.join("data", nombre_archivo)
            
            df.to_csv(ruta_guardado)
            print(f"✅ Guardado: {ruta_guardado} ({len(df)} filas)")

if __name__ == "__main__":
    main()