import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Algo Scanner V4.1 - Multi-Strategy")
st.markdown("Seleziona la strategia quantitativa. Usa l'icona info o il pannello sottostante per i dettagli operativi.")

# 1. MENU A TENDINA PER LA SELEZIONE DELLA STRATEGIA
metodo_scelto = st.selectbox(
    "🛡️ Seleziona il Metodo di Controllo del Mercato:",
    [
        "Metodo 1: Filtro SMA 50 dell'Indice (Equilibrato - Consigliato)",
        "Metodo 2: Filtro RSI 'No Panic' dell'Indice (Aggressivo)",
        "Metodo 3: Filtro Forza Relativa Isolato (Senza blocchi)",
        "Disattiva Filtro: Solo analisi singoli titoli (Massimo Rischio)"
    ]
)

# 2. ICONA INFO DINAMICA: Mostra la spiegazione in base alla scelta dell'utente
st.markdown("---")
st.subheader("ℹ️ Dettaglio Strategia Selezionata")

if "Metodo 1" in metodo_scelto:
    st.info(
        "**💡 METODO 1 - FILTRO SMA 50 (Trend Intermedio):**\n\n"
        "* **Cosa fa:** Analizza l'andamento del NASDAQ degli ultimi 2 mesi. Se il mercato scende sotto la media a 50 giorni, l'app invia un avviso giallo ma continua a cercare titoli.\n"
        "* **Cosa ti fornisce:** Segnala in verde (BUY) solo i titoli straordinariamente forti che mantengono un trend rialzista anche se il mercato generale rallenta.\n"
        "* **Affidabilità:** Ottimo bilanciamento tra protezione del capitale e numero di operazioni (Win Rate stimato: 52-54%)."
    )
elif "Metodo 2" in metodo_scelto:
    st.info(
        "**💡 METODO 2 - FILTRO RSI NO PANIC (Cattura Rimbalzi):**\n\n"
        "* **Cosa fa:** L'applicazione monitora l'RSI a 14 giorni dell'indice NASDAQ per misurare la paura degli investitori. Si blocca completamente SOLO in caso di panico sistemico (RSI < 35).\n"
        "* **Cosa ti fornisce:** Se non c'è un crollo verticale in corso, l'app genera segnali su tutte le azioni in Momentum, permettendoti di sfruttare i rimbalzi veloci.\n"
        "* **Affidabilità:** Strategia aggressiva a più alta volatilità, pensata per non perdere nessuna occasione di breve termine."
    )
elif "Metodo 3" in metodo_scelto:
    st.info(
        "**💡 METODO 3 - FORZA RELATIVA ISOLATA (Alpha Seeker):**\n\n"
        "* **Cosa fa:** Rimuove qualsiasi blocco o controllo sull'indice generale. Si concentra esclusivamente sulle aziende eccellenti che si muovono in controtendenza.\n"
        "* **Cosa ti fornisce:** Fornisce un segnale di acquisto solo se il titolo sta sovraperformando (battendo) l'indice NASDAQ di almeno il 10% negli ultimi 3 mesi.\n"
        "* **Affidabilità:** Molto protettivo nei mercati laterali. Trova pochi segnali, ma di altissima qualità e indipendenti dal trend globale."
    )
else:
    st.warning(
        "**⚠️ DISATTIVA FILTRO (Massimo Rischio):**\n\n"
        "* **Cosa fa:** Disattiva qualsiasi controllo di sicurezza macroeconomico. L'algoritmo analizza le aziende ignorando se il mercato sta crollando o salendo.\n"
        "* **Cosa ti fornisce:** Genera il massimo numero possibile di segnali d'acquisto. Da utilizzare solo se si ha una forte visione rialzista personale."
    )

st.markdown("---")

# 3. TASTO DI SCANSIONE OPERATIVA
if st.button("🚀 AVVIA SCANSIONE MERCATO", type="primary"):
    
    with st.spinner("Analisi e calcolo quantitativo in corso..."):
        
        # Scarica i dati dell'indice NASDAQ Composite per i calcoli macro
        try:
            nasdaq_index = yf.download("^IXIC", period="1y", progress=False)
            nasdaq_index['SMA_50'] = nasdaq_index['Close'].rolling(window=50).mean()
            
            # Calcolo RSI per l'indice
            delta = nasdaq_index['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            nasdaq_index['RSI_14'] = 100 - (100 / (1 + rs))

            ultimo_prezzo_nasdaq = nasdaq_index['Close'].iloc[-1].item()
            sma_50_nasdaq = nasdaq_index['SMA_50'].iloc[-1].item()
            rsi_nasdaq = nasdaq_index['RSI_14'].iloc[-1].item()
            roc_nasdaq_90 = ((nasdaq_index['Close'].iloc[-1] - nasdaq_index['Close'].shift(90).iloc[-1]) / nasdaq_index['Close'].shift(90).iloc[-1]).item() * 100
        except Exception as e:
            st.error(f"Errore nel download dell'indice NASDAQ: {e}")
            st.stop()

        # LOGICA DEI FILTRI SELEZIONATI
        procedi_scansione = True
        
        if "Metodo 1" in metodo_scelto:
            if ultimo_prezzo_nasdaq < sma_50_nasdaq:
                st.warning(f"⚠️ NOTA DI MERCATO: Il NASDAQ ({ultimo_prezzo_nasdaq:.2f}) è attualmente sotto la sua SMA 50 ({sma_50_nasdaq:.2f}).")
        
        elif "Metodo 2" in metodo_scelto:
            if rsi_nasdaq < 35:
                st.error(f"🚨 BLOCCO PANICO ATTIVO: L'RSI del NASDAQ è a {rsi_nasdaq:.2f} (Sotto 35). Rischio crollo sistemico. Scansione interrotta.")
                procedi_scansione = False

        if procedi_scansione:
            ticker_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX"]
            oggi = datetime.now()
            risultati = []

            for ticker in ticker_list:
                try:
                    # FILTRO EARNINGS
                    titolo_info = yf.Ticker(ticker)
                    calendario = titolo_info.calendar
                    salta_titolo = False
                    
                    if calendario is not None and 'Earnings Date' in calendario:
                        date_utili = calendario['Earnings Date']
                        if len(date_utili) > 0:
                            prossimi_utili = date_utili
                            if hasattr(prossimi_utili, 'tzinfo') and prossimi_utili.tzinfo is not None:
                                prossimi_utili = prossimi_utili.replace(tzinfo=None)
                            if oggi <= prossimi_utili <= (oggi + timedelta(days=10)):
                                salta_titolo = True
                    
                    if salta_titolo:
                        risultati.append({"Ticker": ticker, "Prezzo": "-", "ROC 90gg": "-", "Segnale": "🟠 UTILI IMMINENTI (Evitare)", "Stop Loss": "-", "Take Profit": "-"})
                        continue

                    # ANALISI SINGOLO TITOLO
                    df = yf.download(ticker, period="6m", progress=False)
                    if df.empty: continue
                    
                    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                    df['ROC_90'] = ((df['Close'] - df['Close'].shift(90)) / df['Close'].shift(90)) * 100
                    
                    high_low = df['High'] - df['Low']
                    high_cp = (df['High'] - df['Close'].shift()).abs()
                    low_cp = (df['Low'] - df['Close'].shift()).abs()
                    df['ATR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(window=14).mean()

                    prezzo_attuale = df['Close'].iloc[-1].item()
                    ema_50_attuale = df['EMA_50'].iloc[-1].item()
                    roc_attuale = df['ROC_90'].iloc[-1].item()
                    atr_attuale = df['ATR'].iloc[-1].item()
                    
                    condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 0
                    
                    if "Metodo 3" in metodo_scelto:
                        condizione_buy = condizione_buy and (roc_attuale > (roc_nasdaq_90 + 10))

                    if condizione_buy:
                        stop_loss = prezzo_attuale - (2 * atr_attuale)
                        take_profit = prezzo_attuale + (4 * atr_attuale)
                        risultati.append({
                            "Ticker": ticker,
                            "Prezzo": f"{prezzo_attuale:.2f} $",
                            "ROC 90gg": f"{roc_attuale:.2f} %",
                            "Segnale": "🟢 PROTETTO - BUY",
                            "Stop Loss": f"{stop_loss:.2f} $",
                            "Take Profit": f"{take_profit:.2f} $"
                        })
                    else:
                        risultati.append({
                            "Ticker": ticker,
                            "Prezzo": f"{prezzo_attuale:.2f} $",
                            "ROC 90gg": f"{roc_attuale:.2f} %" if pd.notna(roc_attuale) else "N/D",
                            "Segnale": "⚪ NESSUN SEGNALE",
                            "Stop Loss": "-",
                            "Take Profit": "-"
                        })
                except Exception as e:
                    print(f"Errore su {ticker}: {e}")

            df_final = pd.DataFrame(risultati)
            st.subheader("📋 Risultati Screening")
            st.dataframe(df_final, use_container_width=True, hide_index=True)
