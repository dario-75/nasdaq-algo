import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Algo Scanner V3 - Professional")
st.markdown("Algoritmo quantitativo a breve termine (1-3 mesi) con filtri di protezione Macro ed Earnings.")

# Tasto di Scansione nell'interfaccia web
if st.button("🚀 AVVIA SCANSIONE E CALCOLA LIVELLI IN TEMPO REALE", type="primary"):
    
    with st.spinner("Analisi del mercato e calcolo dei parametri quantitativi in corso..."):
        
        # 1. CONTROLLO MACRO: Verifica trend del NASDAQ Composite
        try:
            nasdaq_index = yf.download("^IXIC", period="1y", progress=False)
            nasdaq_index['SMA_200'] = nasdaq_index['Close'].rolling(window=200).mean()
            
            ultimo_prezzo_nasdaq = nasdaq_index['Close'].iloc[-1].item()
            sma_200_nasdaq = nasdaq_index['SMA_200'].iloc[-1].item()
            
            if ultimo_prezzo_nasdaq < sma_200_nasdaq:
                st.error("⚠️ SCANSIONE BLOCCATA: L'indice NASDAQ si trova sotto la Media Mobile a 200 giorni. Il mercato generale è in un trend ribassista. L'algoritmo congela gli acquisti per proteggere il capitale.")
                st.stop()
            else:
                st.success("✅ CONDURRE OPERAZIONI: Il mercato generale è in trend rialzista (Sopra SMA 200).")
        except Exception as e:
            st.error(f"Errore nel controllo macro del mercato: {e}")
            st.stop()

        # Lista delle principali azioni leader del NASDAQ
        ticker_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX"]
        oggi = datetime.now()
        risultati = []

        for ticker in ticker_list:
            try:
                # 2. FILTRO EARNINGS: Controllo calendario trimestrali
                titolo_info = yf.Ticker(ticker)
                calendario = titolo_info.calendar
                salta_titolo = False
                
                if calendario is not None and 'Earnings Date' in calendario:
                    date_utili = calendario['Earnings Date']
                    if len(date_utili) > 0:
                        prossimi_utili = date_utili
                        if hasattr(prossimi_utili, 'tzinfo') and prossimi_utili.tzinfo is not None:
                            prossimi_utili = prossimi_utili.replace(tzinfo=None)
                        
                        # Se mancano meno di 10 giorni agli utili, congeliamo il titolo
                        if oggi <= prossimi_utili <= (oggi + timedelta(days=10)):
                            salta_titolo = True
                
                if salta_titolo:
                    risultati.append({
                        "Ticker": ticker,
                        "Prezzo Attuale": "-",
                        "ROC 90gg": "-",
                        "Stato / Segnale": "🟠 SALTATO (Utili Imminenti)",
                        "Stop Loss (ATR)": "-",
                        "Take Profit": "-"
                    })
                    continue

                # 3. ANALISI TECNICA E CALCOLO SEGNALI
                df = yf.download(ticker, period="6m", progress=False)
                if df.empty: continue
                
                df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                df['ROC_90'] = ((df['Close'] - df['Close'].shift(90)) / df['Close'].shift(90)) * 100
                
                # Calcolo ATR a 14 periodi per la volatilità
                high_low = df['High'] - df['Low']
                high_cp = (df['High'] - df['Close'].shift()).abs()
                low_cp = (df['Low'] - df['Close'].shift()).abs()
                df_atr = pd.concat([high_low, high_cp, low_cp], axis=1)
                true_range = df_atr.max(axis=1)
                df['ATR'] = true_range.rolling(window=14).mean()

                prezzo_attuale = df['Close'].iloc[-1].item()
                ema_50_attuale = df['EMA_50'].iloc[-1].item()
                roc_attuale = df['ROC_90'].iloc[-1].item()
                atr_attuale = df['ATR'].iloc[-1].item()
                
                # Verifica delle condizioni di Momentum
                if prezzo_attuale > ema_50_attuale and roc_attuale > 0:
                    stop_loss = prezzo_attuale - (2 * atr_attuale)
                    take_profit = prezzo_attuale + (4 * atr_attuale)
                    
                    risultati.append({
                        "Ticker": ticker,
                        "Prezzo Attuale": f"{prezzo_attuale:.2f} $",
                        "ROC 90gg": f"{roc_attuale:.2f} %",
                        "Stato / Segnale": "🟢 PROTETTO - BUY",
                        "Stop Loss (ATR)": f"{stop_loss:.2f} $",
                        "Take Profit": f"{take_profit:.2f} $"
                    })
                else:
                    risultati.append({
                        "Ticker": ticker,
                        "Prezzo Attuale": f"{prezzo_attuale:.2f} $",
                        "ROC 90gg": f"{roc_attuale:.2f} %" if pd.notna(roc_attuale) else "N/D",
                        "Stato / Segnale": "⚪ NESSUN SEGNALE",
                        "Stop Loss (ATR)": "-",
                        "Take Profit": "-"
                    })
            except Exception as e:
                print(f"Errore su {ticker}: {e}")

        # Mostra i risultati finali in una splendida tabella web interattiva
        df_final = pd.DataFrame(risultati)
        st.subheader("📋 Pannello Segnali Generati")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.info("💡 Copia i valori di Stop Loss e Take Profit direttamente sulla tua piattaforma di trading per gestire il rischio in modo ottimale.")
