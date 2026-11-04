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
    retornos = []
    dias_invertido = 0
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
            dias_invertido += 1
            
            # Stop Loss
            if (precio_cierre - precio_entrada) / precio_entrada <= -stop_loss_pct:
                en_posicion = False
                retornos.append(-stop_loss_pct - (comision_pct * 2))
                continue
                
            # Salidas
            vender = False
            if tipo_estrategia == "RSI2" and df['Sell_RSI2'].iloc[i]: vender = True
            elif tipo_estrategia == "D7" and df['Sell_D7'].iloc[i]: vender = True
                
            if dias_en_posicion >= max_dias: vender = True
                
            if vender:
                en_posicion = False
                retorno_bruto = (precio_cierre - precio_entrada) / precio_entrada
                retornos.append(retorno_bruto - (comision_pct * 2))
                
    # Calcular exposición (% de días en el mercado)
    total_dias = len(df) - 200
    exposicion = (dias_invertido / total_dias) * 100 if total_dias > 0 else 0
    
    return retornos, exposicion

def calcular_kpis(retornos, exposicion, años_totales=24):
    if not retornos:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0
    
    trades = len(retornos)
    win_rate = (sum(1 for r in retornos if r > 0) / trades) * 100
    retorno_compuesto = (np.prod([1 + r for r in retornos]) - 1) * 100
    peor_trade = min(retornos) * 100
    
    # CAGR (Retorno Anualizado Compuesto)
    cagr = (((1 + retorno_compuesto/100) ** (1 / años_totales)) - 1) * 100
    
    return trades, win_rate, retorno_compuesto, peor_trade, exposicion, cagr

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

        # Calcular años reales de histórico para el CAGR
        años_hist = (df.index[-1] - df.index[200]).days / 365.25

        rets_rsi2, exp_rsi2 = simular_operaciones(df, "RSI2")
        t_rsi, wr_rsi, rc_rsi, pt_rsi, exp_rsi2, cagr_rsi2 = calcular_kpis(rets_rsi2, exp_rsi2, años_hist)

        rets_d7, exp_d7 = simular_operaciones(df, "D7")
        t_d7, wr_d7, rc_d7, pt_d7, exp_d7, cagr_d7 = calcular_kpis(rets_d7, exp_d7, años_hist)

        bh_ret = ((df['Close'].iloc[-1] / df['Close'].iloc[200]) - 1) * 100
        bh_cagr = (((1 + bh_ret/100) ** (1 / años_hist)) - 1) * 100

        resultados.append({
            "Ticker": ticker,
            "B&H_Ret_%": round(bh_ret, 1),
            "B&H_CAGR_%": round(bh_cagr, 1),
            "RSI2_Trades": t_rsi,
            "RSI2_CAGR_%": round(cagr_rsi2, 1),
            "RSI2_Exposure_%": round(exp_rsi2, 1),
            "RSI2_MaxDD_%": round(pt_rsi, 1),
            "D7_Trades": t_d7,
            "D7_CAGR_%": round(cagr_d7, 1),
            "D7_Exposure_%": round(exp_d7, 1),
            "D7_MaxDD_%": round(pt_d7, 1)
        })

    df_resumen = pd.DataFrame(resultados)
    df_resumen.to_csv("results/kpis_backtest.csv", index=False)
    print("✅ Backtest finalizado con métricas de eficiencia (CAGR y Exposure).")

if __name__ == "__main__":
    procesar_estrategias()