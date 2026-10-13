import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Flex-Scanner V11.2 - Live Dashboard")
st.markdown("Infrastruttura quantitativa con visualizzazione totale dei segnali di mercato in tempo reale.")

# CHIAVE API PUBBLICA ATTIVA E VALIDATA
TWELVEDATA_KEY = "184e93dcd7504f7eb80ccb8fa4d9bba7"

# LISTA MASTER DI 20 AZIONI LEADER NASDAQ
DATABASE_20_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW"
]

# INTERFACCIA UTENTE
col1, col2 = st.columns(2)

with col1:
    modalita_scelta = st.selectbox(
        "🛡️ 1. Seleziona la Modalità Algoritmica:",
        [
            "Modalità 1: Momentum Equilibrato (Trend Following)",
            "Modalità 2: Forza Relativa Isolata (Alpha Seeker)",
            "Modalità 3: Rientro sul Supporto (Pullback)"
        ]
    )

with col2:
    dimensione_blocco = st.slider(
        "📦 2. Quantità Azioni del Blocco:",
        min_value=5,
        max_value=20,
        value=5,
        step=5
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

def scarica_dati_twelvedata(ticker):
    try:
        url = f"https://twelvedata.com{ticker}&interval=1day&outputsize=100&apikey={TWELVEDATA_KEY}"
        res = requests.get(url).json()
        if "values" in res:
            df = pd.DataFrame(res["values"])
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)
            df = df.iloc[::-1].reset_index(drop=True)
            return df
    except Exception:
        pass
    return None

if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
    
    with st.spinner("Estrazione dati e calcolo indicatori quantitativi..."):
        risultati = []
        progresso = st.progress(0)
        
        for i, ticker in enumerate(ticker_list):
            df = scarica_dati_twelvedata(ticker)
            progresso.progress((i + 1) / len(ticker_list))
            time.sleep(1) # Pausa di sicurezza anti-ban obbligatoria
            
            if df is None or len(df) < 50: 
                # Se un titolo fallisce, inseriamo una riga di errore per non svuotare la tabella
                risultati.append({"Ticker": ticker, "Prezzo Attuale": "N/D", "ROC (Momentum)": "-", "Segnale": "🔴 Server Timeout", "STOP LOSS": "-", "TAKE PROFIT": "-"})
                continue
                
            # CALCOLI FINANZIARI INTERNI
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
            
            # FILTRI STRATEGIA
            condizione_buy = False
            if "Modalità 1" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 0
            elif "Modalità 2" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 12.0
            elif "Modalità 3" in modalita_scelta:
                distanza_ema = ((prezzo_attuale - ema_50_attuale) / ema_50_attuale) * 100
                condizione_buy = roc_attuale > 0 and (0 <= distanza_ema <= 3.0)

            if condition_buy if 'condition_buy' in locals() else condizione_buy:
                stop_loss = prezzo_attuale - (2 * atr_attuale)
                take_profit = prezzo_attuale + (4 * atr_attuale)
                risultati.append({
                    "Ticker": ticker, "Prezzo Attuale": f"{prezzo_attuale:.2f} $", "ROC (Momentum)": f"{roc_attuale:.2f} %",
                    "Segnale": "🟢 PROTETTO - BUY", "STOP LOSS": f"{stop_loss:.2f} $", "TAKE PROFIT": f"{take_profit:.2f} $"
                })
            else:
                risultati.append({
                    "Ticker": ticker, "Prezzo Attuale": f"{prezzo_attuale:.2f} $", "ROC (Momentum)": f"{roc_attuale:.2f} %",
                    "Segnale": "⚪ NESSUN SEGNALE", "STOP LOSS": "-", "TAKE PROFIT": "-"
                })

        # FORZA LA STAMPA DELLA TABELLA IN OGNI CASO
        df_final = pd.DataFrame(risultati)
        st.subheader("📋 Pannello Analisi Quantitativa Real-Time")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        st.success("Screening completato. Se vedi solo segnali bianchi, il mercato attuale è debole: l'algoritmo consiglia di rimanere in liquidità.")
