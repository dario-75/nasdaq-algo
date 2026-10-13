import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Scanner V15.0 - Enterprise Diagnostic")
st.markdown("Infrastruttura d'élite con controllo automatico dello stato e della validità dei server statunitensi.")

# CHIAVI API FORNITE DALL'UTENTE
AV_KEY = "5JAD1FAAQSH9E72R"
POLYGON_KEY = "iu6rBUvWiGNLdyRj2ZXyDvf7j1ggo_gJ"

# LISTA MASTER DI 30 PANIERE LEADER NASDAQ
DATABASE_30_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW",
    "SBUX", "GILD", "INTU", "MDLZ", "PDD", "REGN", "VRTX", "ISRG", "AMAT", "LRCX"
]

# INTERFACCIA UTENTE: Configurazione dello Scanner
col1, col2, col3 = st.columns(3)

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
            "Yahoo Finance - Canale Ultra-Stable (Istantaneo - Senza Limiti)",
            "Massive / Polygon.io (Dato Istituzionale - Con controllo chiave)",
            "Alpha Vantage (Dato Commerciale - Con controllo chiave)"
        ]
    )

with col3:
    dimensione_blocco = st.slider(
        "📦 3. Quantità Azioni del Blocco:",
        min_value=5, max_value=30, value=5, step=5
    )

# Estrazione blocco base e inserimento manuale
ticker_blocco_base = DATABASE_30_NASDAQ[:dimensione_blocco]
st.markdown("---")
ticker_manuali_input = st.text_input("✍️ Inserisci ticker manuali separati da una virgola (es: PLTR, SMCI):", value="")
ticker_manuali = [t.strip().upper() for t in ticker_manuali_input.split(",") if t.strip()]
ticker_list_completa = list(dict.fromkeys(ticker_blocco_base + ticker_manuali))

if "Alpha Vantage" in server_scelto and len(ticker_list_completa) > 10:
    ticker_list = ticker_list_completa[:10]
    st.sidebar.warning("🔒 Limite Alpha Vantage attivo: ridotto a 10 elementi per proteggere l'API Key.")
else:
    ticker_list = ticker_list_completa

# PANNELLO CONTATORI PREVENTIVI
st.subheader("⏱️ Monitor di Sicurezza del Canale")
tempo_pausa_singola = 0 if "Yahoo" in server_scelto else 12
tempo_totale_stimato = len(ticker_list) * tempo_pausa_singola

metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
with metrics_col1:
    st.metric(label="📈 Azioni Totali in Scansione", value=f"{len(ticker_list)}")
with metrics_col2:
    st.metric(label="⏳ Tempo di Attesa Stimato", value=f"{tempo_totale_stimato} secondi" if tempo_totale_stimato < 60 else f"~{tempo_totale_stimato/60:.1f} minutes")
with metrics_col3:
    st.metric(label="📡 Crediti di Connessione", value="Chiamata Libera" if "Yahoo" in server_scelto else f"{len(ticker_list)} API Credits Richiesti")

st.caption(f"Asset inclusi nella coda: {', '.join(ticker_list)}")
st.markdown("---")

# FUNZIONE DI SCARICO DATI CON VERIFICA INTEGRATA DENTRO L'ALGORITMO
def scarica_dati_con_diagnostica(ticker, server):
    oggi_str = datetime.now().strftime("%Y-%m-%d")
    sei_mesi_fa_str = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    # FEED 1: YAHOO (Non necessita di verifiche chiave)
    if "Yahoo" in server:
        try:
            url = f"https://yahoo.com{ticker}?range=6m&interval=1d"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(url, headers=headers).json()
            timestamps = res['chart']['result']['timestamp']
            indicators = res['chart']['result']['indicators']['quote']
            df = pd.DataFrame({
                'Open': indicators['open'], 'High': indicators['high'], 'Low': indicators['low'],
                'Close': indicators['close'], 'Volume': indicators['volume']
            }, index=pd.to_datetime(timestamps, unit='s')).dropna()
            if len(df) > 20: return df, "Yahoo Finance"
        except Exception: pass

    # FEED 2: ALPHA VANTAGE CON INTERCETTAZIONE LIMITI
    elif "Alpha Vantage" in server:
        try:
            url = f"https://alphavantage.co{ticker}&outputsize=compact&apikey={AV_KEY}"
            res = requests.get(url).json()
            
            # Intercettazione ufficiale del messaggio di superamento limite del piano free
            if "Note" in res or "Information" in res:
                return "LIMITE_RAGGIUNTO", "Alpha Vantage"
                
            if "Time Series (Daily)" in res:
                df = pd.DataFrame.from_dict(res["Time Series (Daily)"], orient='index', dtype=float).sort_index(ascending=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df, "Alpha Vantage"
        except Exception: pass
            
    # FEED 3: MASSIVE CON CONTROLLO VALIDITÀ CHIAVE
    elif "Massive" in server:
        try:
            url = f"https://polygon.io{ticker}/range/1/day/{sei_mesi_fa_str}/{oggi_str}?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_KEY}"
            response_raw = requests.get(url)
            
            # Controllo codice di errore di Massive (403 = chiave non valida o scaduta)
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
    
    with st.spinner("Estrazione, validazione e controllo integrità chiavi..."):
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
            
            # 1. CASO DIAGNOSTICO: CHIAVE MASSIVE BLOCCATA O ERRATA
            if isinstance(df, str) and df == "CHIAVE_NON_VALIDA":
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Chiave Non Valida", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato})
                continue
                
            # 2. CASO DIAGNOSTICO: SUPERAMENTO SOGLIE LIMITI GIORNALIERI (PIANO FREE)
            if isinstance(df, str) and df == "LIMITE_RAGGIUNTO":
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Limite API Raggiunto", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": feed_usato})
                continue
                
            if df is None or len(df) < 20:
                risultati.append({"Ticker": ticker, "Prezzo": "N/D", "ROC": "-", "Segnale": "🔴 Errore Canale", "STOP LOSS": "-", "TAKE PROFIT": "-", "Feed": "N/D"})
                continue
                
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

            if condizione_buy:
                stop_loss = prezzo_attuale - (2 * atr_attuale)
                take_profit = prezzo_attuale + (4 * atr_attuale)
                risultati.append({
                    "Ticker": ticker, "Prezzo": f"{prezzo_attuale:.2f} $", "ROC": f"{roc_attuale:.2f} %",
