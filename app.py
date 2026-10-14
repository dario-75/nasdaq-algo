import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ & MILANO Scanner V16.0 - Global Engine")
st.markdown("Infrastruttura quantitativa multi-valuta ottimizzata per il mercato statunitense ed europeo.")

# CHIAVI API FORNITE DALL'UTENTE (Utilizzate per i canali USA)
AV_KEY = "5JAD1FAAQSH9E72R"
POLYGON_KEY = "iu6rBUvWiGNLdyRj2ZXyDvf7j1ggo_gJ"

# LISTA MASTER DI 30 PANIERE LEADER
DATABASE_30_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW",
    "SBUX", "GILD", "INTU", "MDLZ", "PDD", "REGN", "VRTX", "ISRG", "AMAT", "LRCX"
]

# INTERFACCIA UTENTE: I Menu di Configurazione
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
    server_scelto = st.selectbox(
        "🔌 2. Seleziona il Server da Interrogare:",
        [
            "Yahoo Finance - Canale Ultra-Stable (Consigliato per Italia e USA)",
            "Massive / Polygon.io (Solo Azioni USA - Con controllo chiave)",
            "Alpha Vantage (Solo Azioni USA - Con controllo chiave)"
        ]
    )

st.markdown("---")
st.subheader("📦 Configurazione Universo Azionario")

# ESCLUSIONE RECIPROCA BLOCCHI VS MANUALE
scelta_universo = st.radio(
    "Scegli come inserire le azioni da scansionare (un'opzione esclude l'altra):",
    ["Usa i Blocchi preimpostati NASDAQ (da 5 a 30 azioni)", "Inserimento Manuale Libero (USA e ITALIA .MI)"]
)

ticker_list_base = []

if scelta_universo == "Usa i Blocchi preimpostati NASDAQ (da 5 a 30 azioni)":
    dimensione_blocco = st.slider(
        "Quantità Azioni del Blocco da scansionare:",
        min_value=5, max_value=30, value=5, step=5
    )
    ticker_list_base = DATABASE_30_NASDAQ[:dimensione_blocco]
else:
    ticker_manuali_input = st.text_input(
        "✍️ Digita i simboli separati da una virgola (Usa .MI per l'Italia, es: RACE.MI, STLAM.MI, NVDA):", 
        value="RACE.MI, STLAM.MI"
    )
    ticker_list_base = [t.strip().upper() for t in ticker_manuali_input.split(",") if t.strip()]

# Protezione automatica API Key Alpha Vantage
if "Alpha Vantage" in server_scelto and len(ticker_list_base) > 10:
    ticker_list = ticker_list_base[:10]
else:
    ticker_list = ticker_list_base

# PANNELLO CONTATORI PREVENTIVI IN TEMPO REALE
st.subheader("⏱️ Monitor di Sicurezza del Canale")
tempo_pausa_singola = 0 if "Yahoo" in server_scelto else 12
tempo_totale_stimato = len(ticker_list) * tempo_pausa_singola

metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
with metrics_col1:
    st.metric(label="📈 Azioni Totali in Scansione", value=f"{len(ticker_list)}")
with metrics_col2:
    st.metric(label="⏳ Tempo di Attesa Stimato", value=f"{tempo_totale_stimato} secondi" if tempo_totale_stimato < 60 else f"~{tempo_totale_stimato/60:.1f} minuti")
with metrics_col3:
    st.metric(label="📡 Crediti di Connessione", value="Chiamata Libera" if "Yahoo" in server_scelto else f"{len(ticker_list)} API Credits Richiesti")

st.caption(f"Asset inclusi nella coda: {', '.join(ticker_list)}")
st.markdown("---")

# FUNZIONE DI SCARICO DATI CON VERIFICA INTEGRATA
def scarica_dati_con_diagnostica(ticker, server):
    oggi_str = datetime.now().strftime("%Y-%m-%d")
    sei_mesi_fa_str = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    if "Yahoo" in server:
        try:
            url = f"https://yahoo.com{ticker}?range=6m&interval=1d"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(url, headers=headers).json()
            
            if 'chart' in res and res['chart']['result'] is not None:
                timestamps = res['chart']['result']['timestamp']
                indicators = res['chart']['result']['indicators']['quote'][0]
                
                df = pd.DataFrame({
                    'Open': indicators['open'], 'High': indicators['high'], 'Low': indicators['low'],
                    'Close': indicators['close'], 'Volume': indicators['volume']
                }, index=pd.to_datetime(timestamps, unit='s'))
                
                # Pulizia specifica per i dati italiani ed europei (rimozione righe vuote e riempimento buchi)
                df = df.ffill().bfill().dropna()
                if len(df) > 20: 
                    return df, "Yahoo Finance"
        except Exception as e: 
            print(f"Errore Yahoo su {ticker}: {e}")

    elif "Alpha Vantage" in server:
        if ".MI" in ticker:
            return "SOLO_USA", "Alpha Vantage"
        try:
            url = f"https://alphavantage.co{ticker}&outputsize=compact&apikey={AV_KEY}"
            res = requests.get(url).json()
            if "Note" in res or "Information" in res:
                return "LIMITE_RAGGIUNTO", "Alpha Vantage"
            if "Time Series (Daily)" in res:
                df = pd.DataFrame.from_dict(res["Time Series (Daily)"], orient='index', dtype=float).sort_index(ascending=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df, "Alpha Vantage"
        except Exception: pass
            
    elif "Massive" in server:
        if ".MI" in ticker:
            return "SOLO_USA", "Massive (Polygon)"
        try:
            url = f"https://polygon.io{ticker}/range/1/day/{sei_mesi_fa_str}/{oggi_str}?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_KEY}"
            response_raw = requests.get(url)
            if response_raw.status_code == 403:
                return "CHIAVE_NON_VALIDA", "Massive (Polygon)"
            res = response_raw.json()
            if "status" in res and res["status"] == "ERROR":
                return "LIMITE_RAGGIUNTO", "Massive (Polygon)"
            if "results" in res and len(res["results"]) > 0:
                df = pd.DataFrame(res["results"])[['o', 'h', 'l', 'c', 'v']]
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df.astype(float), "Massive (Polygon)"
        except Exception: pass
            
    return None, "Errore"

# TASTO DI SCANSIONE OPERATIVA
if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
    
    with st.spinner("Estrazione, validazione e calcolo dei mercati globali..."):
        risultati = []
        progresso = st.progress(0)
        pannello_contatori = st.empty()
        
        for i, ticker in enumerate(ticker_list):
            azioni_rimanenti = len(ticker_list) - i
            secondi_rimanenti = azioni_rimanenti * tempo_pausa_singola
            
            with pannello_contatori.container():
                st.info(f"⏳ **STATO SCANNER:** Analisi in corso per **{ticker}**.\n\n"
                        f"• **Titoli mancanti:** {azioni_rimanenti} | • **Tempo residuo:** {secondi_rimanenti} secondi.")
            
            if i > 0 and tempo_pausa_singola > 0:
                time.sleep(tempo_pausa_singola)
                
            df, feed_usato = scarica_dati_con_diagnostica(ticker, server_scelto)
            progresso.progress((i + 1) / len(ticker_list))
            
            # GESTIONE DEGLI ERRORI DIAGNOSTICI
            if isinstance(df, str) and df == "SOLO_USA":
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Usa Server Yahoo per Italia", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato})
                continue
            if isinstance(df, str) and df == "CHIAVE_NON_VALIDA":
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Chiave Non Valida", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato})
                continue
            if isinstance(df, str) and df == "LIMITE_RAGGIUNTO":
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Limite API Raggiunto", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato})
                continue
            if df is None or len(df) < 15:
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Errore Canale / Dati Assenti", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": "N/D"})
                continue
                
            # GESTIONE DINAMICA VALUTA (Euro per Italia, Dollaro per USA)
            valuta = "€" if ".MI" in ticker else "$"
                
            # CALCOLI QUANTITATIVI INTERNI SUL DATO VALIDO
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            periodo_shift = min(30, len(df) - 1)
            df['ROC_90'] = ((df['Close'] - df['Close'].shift(periodo_shift)) / df['Close'].shift(periodo_shift)) * 100 
            
            high_low = df['High'] - df['Low']
            high_cp = (df['High'] - df['Close'].shift()).abs()
            low_cp = (df['Low'] - df['Close'].shift()).abs()
            df['ATR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(window=14).mean()

            prezzo_attuale = float(df['Close'].iloc[-1])
            ema_50_attuale = float(df['EMA_50'].iloc[-1])
            roc_attuale = float(df['ROC_90'].iloc[-1])
            atr_attuale = float(df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else prezzo_attuale * 0.015
            
            # FILTRI STRATEGIA
            condizione_buy = False
            if "Modalità 1" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 0
            elif "Modalità 2" in modalita_scelta:
                condizione_buy = prezzo_attuale > ema_50_attuale and roc_attuale > 12.0
            elif "Modalità 3" in modalita_scelta:
                distanza_ema = ((prezzo_attuale - ema_50_attuale) / ema_50_attuale) * 100
                condizione_buy = roc_attuale > 0 and (0 <= distanza_ema <= 3.0)
            if condizione_buy:
                stop_loss = prezzo_attuale - (2 * atr_attuale)
                take_profit = prezzo_attuale + (4 * atr_attuale)
                risultati.append({
                "Ticker": ticker, "Prezzo": f"{prezzo_attuale:.2f} {valuta}", "ROC": f"{roc_attuale:.2f} %",
                "Segnale": "🟢 PROTETTO - BUY", "STOP LOSS": f"{stop_loss:.2f} {valuta}", "TAKE PROFIT": f"{take_profit:.2f} {valuta}", "Feed": feed_usato
                })
            else:
                risultati.append({
                "Ticker": ticker, "Prezzo": f"{prezzo_attuale:.2f} {valuta}", "ROC": f"{roc_attuale:.2f} %",
                "Segnale": "⚪ NESSUN SEGNALE", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato
                })
                # STAMPA TABELLA DIAGNOSTICATA FINALE
                pannello_contatori.empty()
            if risultati:
                df_final = pd.DataFrame(risultati)
                st.subheader(f"📋 Esito Screening Globale - Multi-Feed Report")
                st.dataframe(df_final, use_container_width=True, hide_index=True)
