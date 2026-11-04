import os
import pandas as pd
import numpy as np

def calcular_rsi(series, period=2):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def simular_operaciones(df, tipo_estrategia="RSI2"):
    """Simula el backtest trade a trade y devuelve una lista de retornos."""
    retornos = []
    en_posicion = False
    precio_entrada = 0.0
    
    # Iteramos desde la fila 200 (para tener SMA200) hasta el final
    for i in range(200, len(df)):
        precio_cierre = df['Close'].iloc[i]
        
        if not en_posicion:
            # Lógica de COMPRA
            if tipo_estrategia == "RSI2":
                if df['Buy_RSI2'].iloc[i]:
                    en_posicion = True
                    precio_entrada = precio_cierre
            elif tipo_estrategia == "D7":
                if df['Buy_D7'].iloc[i]:
                    en_posicion = True
                    precio_entrada = precio_cierre
        else:
            # Lógica de VENTA
            vender = False
            if tipo_estrategia == "RSI2" and df['Sell_RSI2'].iloc[i]:
                vender = True
            elif tipo_estrategia == "D7" and df['Sell_D7'].iloc[i]:
                vender = True
                
            if vender:
                en_posicion = False
                retorno = (precio_cierre - precio_entrada) / precio_entrada
                retornos.append(retorno)
                
    # Si nos quedamos con una posición abierta al final, la cerramos al último precio
    if en_posicion:
        retorno = (df['Close'].iloc[-1] - precio_entrada) / precio_entrada
        retornos.append(retorno)
        
    return retornos

def calcular_kpis(retornos):
    """Calcula las métricas clave a partir de una lista de retornos."""
    if not retornos:
        return 0, 0.0, 0.0, 0.0
    
    trades = len(retornos)
    ganadores = sum(1 for r in retornos if r > 0)
    win_rate = (ganadores / trades) * 100
    retorno_medio = np.mean(retornos) * 100
    retorno_total = np.sum(retornos) * 100
    
    return trades, win_rate, retorno_medio, retorno_total

def procesar_estrategias():
    os.makedirs("results", exist_ok=True)
    archivos = [f for f in os.listdir("data") if f.endswith(".csv")]
    
    resultados = []
    print(f"Ejecutando Backtest en {len(archivos)} activos...")
    
    for archivo in archivos:
        ticker = archivo.replace(".csv", "")
        df = pd.read_csv(f"data/{archivo}", index_col=0, parse_dates=True)
        
        if len(df) < 200: continue
            
        # Indicadores
        df['RSI_2'] = calcular_rsi(df['Close'], period=2)
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Min_7'] = df['Close'].rolling(window=7).min()
        df['Max_7'] = df['Close'].rolling(window=7).max()

        # Señales
        df['Buy_RSI2'] = (df['RSI_2'] < 5) & (df['Close'] > df['SMA_200'])
        df['Sell_RSI2'] = (df['RSI_2'] > 70)
        
        df['Buy_D7'] = (df['Close'] == df['Min_7']) & (df['Close'] > df['SMA_200'])
        df['Sell_D7'] = (df['Close'] == df['Max_7'])

        # Backtest RSI2
        rets_rsi2 = simular_operaciones(df, "RSI2")
        t_rsi, wr_rsi, rm_rsi, rt_rsi = calcular_kpis(rets_rsi2)

        # Backtest Double 7
        rets_d7 = simular_operaciones(df, "D7")
        t_d7, wr_d7, rm_d7, rt_d7 = calcular_kpis(rets_d7)

        resultados.append({
            "Ticker": ticker,
            "RSI2_Trades": t_rsi,
            "RSI2_WinRate_%": round(wr_rsi, 1),
            "RSI2_AvgRet_%": round(rm_rsi, 2),
            "RSI2_TotalRet_%": round(rt_rsi, 1),
            "D7_Trades": t_d7,
            "D7_WinRate_%": round(wr_d7, 1),
            "D7_AvgRet_%": round(rm_d7, 2),
            "D7_TotalRet_%": round(rt_d7, 1)
        })

    # Guardar el resumen con los KPIs
    df_resumen = pd.DataFrame(resultados)
    df_resumen.to_csv("results/kpis_backtest.csv", index=False)
    print("✅ Backtest terminado. KPIs guardados en results/kpis_backtest.csv")

if __name__ == "__main__":
    procesar_estrategias()