import os
import yaml
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

def simular_retornos_diarios(df, tipo_estrategia="RSI2", comision_pct=0.001, stop_loss_pct=0.05, max_dias=10):
    """Simula los retornos diarios de una estrategia, aplicando comisiones y SL."""
    retornos = pd.Series(0.0, index=df.index)
    en_posicion = False
    precio_entrada = 0.0
    dias_en_posicion = 0
    
    for i in range(200, len(df)):
        precio_cierre = df['Close'].iloc[i]
        retorno_dia = 0.0
        
        if not en_posicion:
            if (tipo_estrategia == "RSI2" and df['Buy_RSI2'].iloc[i]) or \
               (tipo_estrategia == "D7" and df['Buy_D7'].iloc[i]):
                en_posicion = True
                precio_entrada = precio_cierre
                dias_en_posicion = 0
                retorno_dia = -comision_pct # Comisión de compra
        else:
            dias_en_posicion += 1
            # Retorno del activo este día
            retorno_dia = (precio_cierre / df['Close'].iloc[i-1]) - 1
            
            # Stop Loss
            if (precio_cierre - precio_entrada) / precio_entrada <= -stop_loss_pct:
                en_posicion = False
                retorno_dia -= comision_pct # Comisión de venta
            else:
                vender = False
                if tipo_estrategia == "RSI2" and df['Sell_RSI2'].iloc[i]: vender = True
                elif tipo_estrategia == "D7" and df['Sell_D7'].iloc[i]: vender = True
                
                if dias_en_posicion >= max_dias: vender = True
                    
                if vender:
                    en_posicion = False
                    retorno_dia -= comision_pct # Comisión de venta
                    
        retornos.iloc[i] = retorno_dia
        
    return retornos

def main():
    capital_inicial = 100000.0 # Empezamos con 100.000€
    
    # 1. Leer la lista de la Cartera Élite
    with open("config/tickers.yaml", "r") as f:
        config = yaml.safe_load(f)
    tickers = config.get("connors_elite", [])
    
    if not tickers:
        print("❌ No se encontró la lista 'connors_elite' en el YAML.")
        return

    print(f"Simulando cartera con {len(tickers)} activos...")
    
    # Diccionarios para guardar los retornos de cada activo
    retornos_rsi2 = {}
    retornos_d7 = {}
    
    for ticker in tickers:
        ruta = f"data/{ticker}.csv"
        if not os.path.exists(ruta): continue
        
        df = pd.read_csv(ruta, index_col=0, parse_dates=True)
        if len(df) < 200: continue
            
        df['RSI_2'] = calcular_rsi(df['Close'], period=2)
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['Min_7'] = df['Close'].rolling(window=7).min()
        df['Max_7'] = df['Close'].rolling(window=7).max()
        
        df['Buy_RSI2'] = (df['RSI_2'] < 5) & (df['Close'] > df['SMA_200'])
        df['Sell_RSI2'] = (df['RSI_2'] > 70)
        df['Buy_D7'] = (df['Close'] == df['Min_7']) & (df['Close'] > df['SMA_200'])
        df['Sell_D7'] = (df['Close'] == df['Max_7'])
        
        retornos_rsi2[ticker] = simular_retornos_diarios(df, "RSI2")
        retornos_d7[ticker] = simular_retornos_diarios(df, "D7")

    # 2. Unir todos los retornos en un solo DataFrame (alineando fechas)
    df_rsi2 = pd.DataFrame(retornos_rsi2).fillna(0)
    df_d7 = pd.DataFrame(retornos_d7).fillna(0)
    
    # 3. Calcular el retorno de la cartera (media ponderada al 50% RSI2 y 50% D7)
    # Nota: Si quieres testearlas por separado, puedes cambiar estos pesos
    port_ret_rsi2 = df_rsi2.mean(axis=1) # Retorno diario medio de la cartera
    port_ret_d7 = df_d7.mean(axis=1)
    
    # Retorno combinado final (50% RSI2, 50% D7)
    port_ret_combinado = (port_ret_rsi2 * 0.5) + (port_ret_d7 * 0.5)
    
    # 4. Calcular la curva de capital (Interés compuesto)
    equity_rsi2 = (1 + port_ret_rsi2).cumprod() * capital_inicial
    equity_d7 = (1 + port_ret_d7).cumprod() * capital_inicial
    equity_comb = (1 + port_ret_combinado).cumprod() * capital_inicial
    
    # 5. Calcular KPIs de la cartera
    def calcular_metricas_cartera(equity, nombre):
        # Max Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_dd = drawdown.min() * 100
        
        # CAGR (Retorno Anualizado Compuesto)
        años = (equity.index[-1] - equity.index[0]).days / 365.25
        total_ret = (equity.iloc[-1] / capital_inicial - 1) * 100
        cagr = (((1 + total_ret/100) ** (1 / años)) - 1) * 100
        
        print(f"\n--- {nombre} ---")
        print(f"Capital Final:  {equity.iloc[-1]:,.0f} €")
        print(f"Retorno Total:  {total_ret:.1f} %")
        print(f"CAGR Anual:     {cagr:.2f} %")
        print(f"Max Drawdown:   {max_dd:.1f} %")
        
        return equity

    print("\n==============================")
    print("  RESULTADOS DE LA CARTERA ÉLITE")
    print("==============================")
    
    equity_rsi2 = calcular_metricas_cartera(equity_rsi2, "Cartera 100% RSI2")
    equity_d7 = calcular_metricas_cartera(equity_d7, "Cartera 100% Double 7")
    equity_comb = calcular_metricas_cartera(equity_comb, "Cartera Combinada (50/50)")

    # 6. Guardar los resultados para poder graficarlos luego
    os.makedirs("results", exist_ok=True)
    df_equity = pd.DataFrame({
        "RSI2": equity_rsi2,
        "Double7": equity_d7,
        "Combinada": equity_comb
    })
    df_equity.to_csv("results/portfolio_equity.csv")
    print("\n✅ Curva de capital guardada en results/portfolio_equity.csv")

if __name__ == "__main__":
    main()
