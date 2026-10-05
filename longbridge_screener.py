import os
import argparse
import pandas as pd
from datetime import datetime
from longbridge.openapi import QuoteContext, Config
import yfinance as yf
import time

def fetch_screener_data(tickers):
    # Inicializar Longbridge
    app_key = os.environ.get("LONGBRIDGE_APP_KEY")
    app_secret = os.environ.get("LONGBRIDGE_APP_SECRET")
    access_token = os.environ.get("LONGBRIDGE_ACCESS_TOKEN")

    ctx = None
    if all([app_key, app_secret, access_token]):
        try:
            config = Config.from_env()
            ctx = QuoteContext(config)
        except Exception as e:
            print(f"Error conectando a Longbridge: {e}")
    else:
        print("Faltan variables de entorno de Longbridge. Se usarán datos de yfinance como respaldo total.")

    results = []
    
    for ticker in tickers:
        print(f"Procesando: {ticker}...")
        
        row = {
            "Ticker": ticker,
            "Último Precio": "N/A",
            "Volumen Diario": "N/A",
            "Capitalización": "N/A",
            "PER (P/E)": "N/A",
            "P/B (P/Book)": "N/A",
            "Máximo 52 Semanas": "N/A",
            "Mínimo 52 Semanas": "N/A",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 1. Datos en tiempo real vía Longbridge
        if ctx:
            try:
                quotes = ctx.quote([ticker])
                if quotes:
                    q = quotes[0]
                    row["Último Precio"] = float(q.last_done) if q.last_done else "N/A"
                    row["Volumen Diario"] = int(q.volume) if q.volume else "N/A"
            except Exception as e:
                print(f"Error en Longbridge para {ticker}: {e}")

        # 2. Datos fundamentales vía yfinance
        try:
            # yfinance no usa el sufijo .US para el mercado americano
            yf_ticker = ticker.replace(".US", "")
            stock = yf.Ticker(yf_ticker)
            info = stock.info
            
            # Respaldo de precio/volumen si Longbridge falló o no retornó datos
            if row["Último Precio"] == "N/A":
                row["Último Precio"] = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            if row["Volumen Diario"] == "N/A":
                row["Volumen Diario"] = info.get('volume', info.get('regularMarketVolume', 'N/A'))
                
            # Extraer fundamentales
            row["Capitalización"] = info.get('marketCap', 'N/A')
            row["PER (P/E)"] = info.get('trailingPE', info.get('forwardPE', 'N/A'))
            row["P/B (P/Book)"] = info.get('priceToBook', 'N/A')
            row["Máximo 52 Semanas"] = info.get('fiftyTwoWeekHigh', 'N/A')
            row["Mínimo 52 Semanas"] = info.get('fiftyTwoWeekLow', 'N/A')
            
        except Exception as e:
            print(f"Error procesando fundamentales para {ticker}: {e}")
            
        results.append(row)
        time.sleep(0.1) # Breve pausa para evitar límites de tasa (rate limits)
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", type=str, required=True, help="Tickers separados por comas")
    args = parser.parse_args()
    
    # Limpieza de los argumentos (espacios y comillas)
    raw_tickers = args.tickers.split(',')
    tickers_list = [t.strip(' "\'') for t in raw_tickers if t.strip(' "\'')]
    
    df = fetch_screener_data(tickers_list)
    
    if not df.empty:
        filename = f"Screener_Longbridge_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ Archivo generado exitosamente: {filename}")
    else:
        print("\n⚠️ Error: No se generaron datos para exportar.")
