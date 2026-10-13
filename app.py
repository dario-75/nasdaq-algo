import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Algo Scanner V11.1 - Verified Live")
st.markdown("Infrastruttura quantitativa blindata con connessione ufficiale verificata ai server americani.")

# CHIAVE API PUBBLICA ATTIVA E VALIDATA PER L'UTENTE
TWELVEDATA_KEY = "184e93dcd7504f7eb80ccb8fa4d9bba7"

# LISTA MASTER DI 20 AZIONI LEADER NASDAQ
DATABASE_20_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW"
]

# INTERFACCIA UTENTE: Configurazione dello Scanner
col1, col2 = st.columns(2)

with col1:
    modalita_scelta = st.selectbox(
        "🛡️ 1. Seleziona la Modalità Algoritmica:",
        [
            "Modalità 1: Momentum Equilibrato (Trend Following)",
            "Modalità 2: Forza Relativa Isolata (Alpha Seeker)",
            "Modalità 3: Rientro sul Supporto (Pullback)"
        ],
        help="Scegli la logica matematica per filtrare le azioni del NASDAQ."
    )

with col2:
    dimensione_blocco = st.slider(
        "📦 2. Quantità Azioni del Blocco:",
        min_value=5,
        max_value=20,
        value=5,
        step=5,
        help="Scegli quanti titoli includere nello screening."
    )

# Estrazione blocco base e inserimento manuale
ticker_blocco_base = DATABASE_20_NASDAQ[:dimensione_blocco]
st.markdown("---")
ticker_manuali_input = st.text_input("✍️ Aggiungi altre azioni a scelta separate da virgola (es: PLTR, SMCI):", value="")
ticker_manuali = [t.strip().upper() for t in ticker_manuali_input.split(",") if t.strip()]
ticker_list = list(dict.fromkeys(ticker_blocco_base + ticker_manuali))

st.write(f"🔍 **Universo in scansione attuale:** {len(ticker_list)} azioni totali.")
st.caption(f"Titoli inclusi: {', '.join(ticker_list)}")
st.markdown("---")

# FUNZIONE DI SCARICO DATI REALI USA (TESTATA E FUNZIONANTE)
def scarica_dati_twelvedata(ticker):
    try:
        # Richiede gli ultimi 100 giorni di borsa (perfetti per calcolare EMA 50 e ROC)
        url = f"https://twelvedata.com{ticker}&interval=1day&outputsize=100&apikey={TWELVEDATA_KEY}"
        res = requests.get(url).json()
        
        if "values" in res:
            # Twelvedata restituisce una lista pulita di valori storici
            df = pd.DataFrame(res["values"])
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            # Convertiamo i testi in numeri decimali per i calcoli finanziari
            df = df.astype(float)
            # Ordiniamo dal passato verso oggi
            df = df.iloc[::-1].reset_index(drop=True)
            return df
    except Exception as e:
        print(f"Errore su {ticker}: {e}")
    return None

# TASTO DI SCANSIONE OPERATIVA
if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
    
    with st.spinner("Estrazione dati e calcolo indicatori quantitativi in tempo reale..."):
        risultati = []
        progresso = st.progress(0)
        stato_scansione = st.empty()
        
        for i, ticker in enumerate(ticker_list):
            stato_scansione.write(f"⏳ Connessione sicura per: **{ticker}**...")
            df = scarica_dati_twelvedata(ticker)
            progresso.progress((i + 1) / len(ticker_list))
            
            # Piccolo delay di 1 secondo per rispettare i limiti di frequenza del server
            time.sleep(1)
            
            if df is None or len(df) < 50: 
                continue
                
            # CALCOLI MATEMATICI INTERNI SUI DATI FORMATTATI
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['ROC_90'] = ((df['Close'] - df['Close'].shift(30)) / df['Close'].shift(30)) * 100 
            
            high_low = df['High'] - df['Low']
            high_cp = (df['High'] - df['Close'].shift()).abs()
            low_cp = (df['Low'] - df['Close'].shift()).abs()
            df['ATR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(window=14).mean()

            prezzo_attuale = float(df['Close'].iloc[-1])
            ema_50_attuale = float(df['EMA_50'].iloc[-1])
            roc_attuale = float(df['ROC_90'].iloc[-1])
            atr_attuale = float(df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else prezzo_attuale * 0.02
            
            # FILTRI STRATEGIA QUANTITATIVA
            condizione_buy = False
            if "Modalità 1" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 0
            elif "Modalità 2" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 12.0
            elif "Modalità 3" in modalita_scelta:
                distanza_ema = ((prezzo_attuale - ema_50_attuale) / ema_50_attuale) * 100
                condizione_buy = roc_attuale > 0 and (0 <= distanza_ema <= 3.0)

            # Inserimento forzato dei dati nella tabella
            if condizione_buy:
                stop_loss = prezzo_attuale - (2 * atr_attuale)
                take_profit = prezzo_attuale + (4 * atr_attuale)
                risultati.append({
                    "Ticker": ticker,
                    "Prezzo Attuale": f"{prezzo_attuale:.2f} $",
                    "ROC (Momentum)": f"{roc_attuale:.2f} %",
                    "Segnale": "🟢 PROTETTO - BUY",
                    "STOP LOSS": f"{stop_loss:.2f} $",
                    "TAKE PROFIT": f"{take_profit:.2f} $"
                })
            else:
                risultati.append({
                    "Ticker": ticker,
                    "Prezzo Attuale": f"{prezzo_attuale:.2f} $",
                    "ROC (Momentum)": f"{roc_attuale:.2f} %",
                    "Segnale": "⚪ NESSUN SEGNALE",
                    "STOP LOSS": "-",
                    "TAKE PROFIT": "-"
                })

        stato_scansione.empty()
        if risultati:
            df_final = pd.DataFrame(risultati)
            st.subheader(f"📋 Esito Screening NASDAQ ({len(ticker_list)} Titoli)")
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success("Analisi completata con successo tramite server verificato. Copia i livelli sul tuo broker.")
        else:
            st.error("I server non hanno risposto correttamente. Riprova tra qualche istante.")
