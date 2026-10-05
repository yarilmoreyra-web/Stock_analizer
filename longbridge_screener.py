import os
import argparse
import pandas as pd
from datetime import datetime
from longbridge.openapi import QuoteContext, Config

def fetch_longbridge_data(tickers):
    # 1. Obtener las credenciales directamente del entorno
    app_key = os.environ.get("LONGBRIDGE_APP_KEY")
    app_secret = os.environ.get("LONGBRIDGE_APP_SECRET")
    access_token = os.environ.get("LONGBRIDGE_ACCESS_TOKEN")

    if not all([app_key, app_secret, access_token]):
        print("⚠️ Faltan credenciales. Asegúrate de que los secrets estén configurados.")
        return pd.DataFrame()

    try:
        # 2. Inicializar la configuración de forma explícita
        config = Config(app_key=app_key, app_secret=app_secret, access_token=access_token)
        ctx = QuoteContext(config)
    except Exception as e:
        print(f"Error de autenticación con Longbridge: {e}")
        return pd.DataFrame()
    
    results = []
    
    for ticker in tickers:
        print(f"Consultando datos para: {ticker}...")
        try:
            quotes = ctx.quote([ticker])
            
            if quotes:
                q = quotes[0]
                stock_info = {
                    "Ticker": ticker,
                    "Último Precio": getattr(q, 'last_done', 'N/A'),
                    "Volumen Diario": getattr(q, 'volume', 'N/A'),
                    "Capitalización": getattr(q, 'market_cap', 'N/A'),
                    "PER (P/E)": getattr(q, 'pe', 'N/A'),
                    "P/B (P/Book)": getattr(q, 'pb', 'N/A'),
                    "Máximo 52 Semanas": getattr(q, 'high_52w', 'N/A'),
                    "Mínimo 52 Semanas": getattr(q, 'low_52w', 'N/A'),
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                results.append(stock_info)
            else:
                print(f"No se devolvieron datos de cotización para {ticker}")
                
        except Exception as e:
            print(f"Error procesando {ticker}: {str(e)}")
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extractor de datos fundamentales vía Longbridge")
    parser.add_argument("--tickers", type=str, required=True, 
                        help="Tickers separados por comas. Ej: AAPL.US, TSLA.US")
    args = parser.parse_args()
    
    # 3. Limpieza robusta: divide por coma y elimina espacios y cualquier tipo de comilla
    raw_tickers = args.tickers.split(',')
    tickers_list = [t.strip(' "\'') for t in raw_tickers if t.strip(' "\'')]
    
    df = fetch_longbridge_data(tickers_list)
    
    if not df.empty:
        filename = f"Screener_Longbridge_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ Archivo Excel generado exitosamente: {filename}")
    else:
        print("\n⚠️ No se generaron datos para exportar. Verifica tus credenciales o los tickers.")
