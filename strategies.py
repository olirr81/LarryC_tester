import os
import pandas as pd

def calcular_rsi(series, period=2):
    """Calcula el RSI clásico de Wilder."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    # Usamos media exponencial (EWM) que es el estándar para el RSI
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def procesar_estrategias():
    # 1. Crear carpeta de resultados
    os.makedirs("results", exist_ok=True)
    
    # 2. Listar todos los archivos en data/
    if not os.path.exists("data"):
        print("❌ No existe la carpeta 'data'. Ejecuta primero el downloader.")
        return
        
    archivos = [f for f in os.listdir("data") if f.endswith(".csv")]
    print(f"Analizando {len(archivos)} archivos...")
    
    resumen = []

    for archivo in archivos:
        ticker = archivo.replace(".csv", "")
        df = pd.read_csv(f"data/{archivo}", index_col=0, parse_dates=True)
        
        # Si el CSV está vacío o le faltan datos, saltar
        if len(df) < 200:
            continue
            
        # --- INDICADORES ---
        df['RSI_2'] = calcular_rsi(df['Close'], period=2)
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Min_7'] = df['Close'].rolling(window=7).min()
        df['Max_7'] = df['Close'].rolling(window=7).max()

        # --- SEÑALES RSI2 ---
        # Compra: RSI2 < 5 y Precio > SMA200 (Tendencia alcista)
        df['Buy_RSI2'] = (df['RSI_2'] < 5) & (df['Close'] > df['SMA_200'])
        # Venta: RSI2 > 70 (o salida cuando cruza 30, usamos 70 como salida rápida típica)
        df['Sell_RSI2'] = (df['RSI_2'] > 70) 

        # --- SEÑALES DOUBLE 7 ---
        # Compra: Mínimo de 7 días y Precio > SMA200
        df['Buy_D7'] = (df['Close'] == df['Min_7']) & (df['Close'] > df['SMA_200'])
        # Venta: Máximo de 7 días
        df['Sell_D7'] = (df['Close'] == df['Max_7'])

        # --- GUARDAR RESULTADOS ---
        # Guardamos el archivo con las señales calculadas
        df.to_csv(f"results/{ticker}_signals.csv")
        
        # Contar cuántas señales ha habido históricamente
        total_rsi2 = df['Buy_RSI2'].sum()
        total_d7 = df['Buy_D7'].sum()
        
        resumen.append({
            "Ticker": ticker,
            "Total_RSI2_Buys": total_rsi2,
            "Total_Double7_Buys": total_d7
        })

    # 3. Guardar un resumen global
    df_resumen = pd.DataFrame(resumen)
    df_resumen.to_csv("results/resumen_global.csv", index=False)
    print("✅ Proceso terminado. Revisa la carpeta 'results'.")

if __name__ == "__main__":
    procesar_estrategias()