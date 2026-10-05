import os
import argparse
import pandas as pd
from datetime import datetime
from longbridge.openapi import QuoteContext, Config

def fetch_longbridge_data(tickers):
    # La configuración se nutre de forma automática de las variables de entorno
    # Asegúrate de configurar: LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN
    try:
        config = Config.from_env()
        ctx = QuoteContext(config)
    except Exception as e:
        print(f"Error de autenticación con Longbridge: {e}")
        return pd.DataFrame()
    
    results = []
    
    for ticker in tickers:
        print(f"Consultando datos para: {ticker}...")
        try:
            # 1. Obtener datos de cotización (Market Data, Valuation básica)
            quotes = ctx.quote([ticker])
            
            if quotes:
                q = quotes[0]
                # 2. Estructurar los campos (adaptado a los atributos del SDK)
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
    parser = argparse.ArgumentParser(description="Extractor de datos fundamentales vía Longbridge OpenAPI")
    parser.add_argument("--tickers", type=str, required=True, 
                        help="Tickers separados por comas. Ej: AAPL.US,TSLA.US,O.US")
    args = parser.parse_args()
    
    # Limpiar y preparar la lista
    tickers_list = [t.strip().upper() for t in args.tickers.split(',')]
    
    df = fetch_longbridge_data(tickers_list)
    
    if not df.empty:
        # Exportación del archivo
        filename = f"Screener_Longbridge_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ Archivo Excel generado exitosamente: {filename}")
    else:
        print("\n⚠️ No se generaron datos para exportar. Verifica tus credenciales o tickers.")
