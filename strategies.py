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

def simular_operaciones(df, tipo_estrategia="RSI2", comision_pct=0.001, stop_loss_pct=0.03, max_dias=10):
    """Simula operaciones con Stop Loss y Salida por Tiempo."""
    retornos = []
    en_posicion = False
    precio_entrada = 0.0
    dias_en_posicion = 0
    
    for i in range(200, len(df)):
        precio_cierre = df['Close'].iloc[i]
        
        if not en_posicion:
            if (tipo_estrategia == "RSI2" and df['Buy_RSI2'].iloc[i]) or \
               (tipo_estrategia == "D7" and df['Buy_D7'].iloc[i]):
                en_posicion = True
                precio_entrada = precio_cierre
                dias_en_posicion = 0
        else:
            dias_en_posicion += 1
            
            # 1. Comprobar Stop Loss (usando el precio de cierre o el mínimo del día)
            if (precio_cierre - precio_entrada) / precio_entrada <= -stop_loss_pct:
                en_posicion = False
                retorno = -stop_loss_pct - (comision_pct * 2)
                retornos.append(retorno)
                continue
                
            # 2. Comprobar Salida Normal
            vender = False
            if tipo_estrategia == "RSI2" and df['Sell_RSI2'].iloc[i]:
                vender = True
            elif tipo_estrategia == "D7" and df['Sell_D7'].iloc[i]:
                vender = True
                
            # 3. Comprobar Salida por Tiempo (Time Stop)
            if dias_en_posicion >= max_dias:
                vender = True
                
            if vender:
                en_posicion = False
                retorno_bruto = (precio_cierre - precio_entrada) / precio_entrada
                retorno_neto = retorno_bruto - (comision_pct * 2) 
                retornos.append(retorno_neto)
                
    return retornos

def calcular_kpis(retornos):
    if not retornos:
        return 0, 0.0, 0.0, 0.0, 0.0
    
    trades = len(retornos)
    ganadores = sum(1 for r in retornos if r > 0)
    win_rate = (ganadores / trades) * 100
    retorno_medio = np.mean(retornos) * 100
    retorno_compuesto = (np.prod([1 + r for r in retornos]) - 1) * 100
    peor_trade = min(retornos) * 100
    
    return trades, win_rate, retorno_medio, retorno_compuesto, peor_trade

def procesar_estrategias():
    os.makedirs("results", exist_ok=True)
    archivos = [f for f in os.listdir("data") if f.endswith(".csv")]
    
    resultados = []
    
    for archivo in archivos:
        ticker = archivo.replace(".csv", "")
        df = pd.read_csv(f"data/{archivo}", index_col=0, parse_dates=True)
        
        if len(df) < 200: continue
            
        df['RSI_2'] = calcular_rsi(df['Close'], period=2)
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Min_7'] = df['Close'].rolling(window=7).min()
        df['Max_7'] = df['Close'].rolling(window=7).max()

        df['Buy_RSI2'] = (df['RSI_2'] < 5) & (df['Close'] > df['SMA_200'])
        df['Sell_RSI2'] = (df['RSI_2'] > 70)
        
        df['Buy_D7'] = (df['Close'] == df['Min_7']) & (df['Close'] > df['SMA_200'])
        df['Sell_D7'] = (df['Close'] == df['Max_7'])

        # Backtest con Stop Loss del 3% y Máximo 10 días
        rets_rsi2 = simular_operaciones(df, "RSI2", comision_pct=0.001, stop_loss_pct=0.03, max_dias=10)
        t_rsi, wr_rsi, rm_rsi, rc_rsi, pt_rsi = calcular_kpis(rets_rsi2)

        rets_d7 = simular_operaciones(df, "D7", comision_pct=0.001, stop_loss_pct=0.03, max_dias=10)
        t_d7, wr_d7, rm_d7, rc_d7, pt_d7 = calcular_kpis(rets_d7)

        bh_ret = ((df['Close'].iloc[-1] / df['Close'].iloc[200]) - 1) * 100

        resultados.append({
            "Ticker": ticker,
            "B&H_Ret_%": round(bh_ret, 1),
            "RSI2_Trades": t_rsi,
            "RSI2_WinRate_%": round(wr_rsi, 1),
            "RSI2_CompoundRet_%": round(rc_rsi, 1),
            "RSI2_WorstTrade_%": round(pt_rsi, 1),
            "D7_Trades": t_d7,
            "D7_WinRate_%": round(wr_d7, 1),
            "D7_CompoundRet_%": round(rc_d7, 1),
            "D7_WorstTrade_%": round(pt_d7, 1)
        })

    df_resumen = pd.DataFrame(resultados)
    df_resumen.to_csv("results/kpis_backtest.csv", index=False)
    print("✅ Backtest con Stop Loss y Time Stop terminado.")

if __name__ == "__main__":
    procesar_estrategias()