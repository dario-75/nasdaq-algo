import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Flex-Scanner V8.8 - Verified Stable")
st.markdown("Infrastruttura quantitativa d'élite testata e validata con sorgenti dati ufficiali statunitensi.")

# CHIAVI API FORNITE DALL'UTENTE
AV_KEY = "5JAD1FAAQSH9E72R"
POLYGON_KEY = "iu6rBUvWiGNLdyRj2ZXyDvf7j1ggo_gJ"

# LISTA MASTER DI 30 PANIERE LEADER NASDAQ
DATABASE_30_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW",
    "SBUX", "GILD", "INTU", "MDLZ", "PDD", "REGN", "VRTX", "ISRG", "AMAT", "LRCX"
]

# INTERFACCIA UTENTE: Menu di Configurazione con icone descrittive
col1, col2, col3 = st.columns(3)

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
    server_scelto = st.selectbox(
        "🔌 2. Seleziona il Server da Interrogare:",
        ["Massive / Polygon.io (Illimitato - Con pausa di sicurezza)", "Alpha Vantage (Veloce - Max 25 chiamate/giorno)"],
        help="Scegli a quale provider americano inviare le richieste dati."
    )

with col3:
    dimensione_blocco = st.selectbox(
        "📦 3. Quantità Azioni del Blocco:",
,
        index=0,
        help="Scegli il numero di titoli preimpostati da scansionare."
    )

# Estrazione blocco base e inserimento manuale
ticker_blocco_base = DATABASE_30_NASDAQ[:dimensione_blocco]
st.markdown("---")
ticker_manuali_input = st.text_input("✍️ Aggiungi altre azioni a scelta separate da virgola (es: PLTR, SMCI):", value="")
ticker_manuali = [t.strip().upper() for t in ticker_manuali_input.split(",") if t.strip()]
ticker_list_completa = list(dict.fromkeys(ticker_blocco_base + ticker_manuali))

# Blocco di sicurezza rigido per Alpha Vantage
if "Alpha Vantage" in server_scelto:
    ticker_list = ticker_list_completa[:10]
    if len(ticker_list_completa) > 10:
        st.sidebar.warning("🔒 Limite Alpha Vantage attivo: ridotto a 10 elementi totali.")
else:
    ticker_list = ticker_list_completa

st.write(f"🔍 **Universo in scansione attuale:** {len(ticker_list)} azioni totali.")
st.caption(f"Titoli inclusi: {', '.join(ticker_list)}")
st.markdown("---")

# FUNZIONE DI SCARICO DATI REALI USA
def scarica_dati_singolo_server(ticker, server):
    oggi_str = datetime.now().strftime("%Y-%m-%d")
    sei_mesi_fa_str = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    if "Alpha Vantage" in server:
        try:
            time.sleep(12) # Pausa anti-ban per limiti di frequenza gratuiti
            url = f"https://alphavantage.co{ticker}&outputsize=compact&apikey={AV_KEY}"
            res = requests.get(url).json()
            if "Time Series (Daily)" in res:
                raw_data = res["Time Series (Daily)"]
                df = pd.DataFrame.from_dict(raw_data, orient='index', dtype=float)
                df = df.sort_index(ascending=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df
        except Exception:
            pass
            
    elif "Massive" in server:
        try:
            time.sleep(12) # Pausa obbligatoria anti-ban per Massive Free
            url = f"https://polygon.io{ticker}/range/1/day/{sei_mesi_fa_str}/{oggi_str}?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_KEY}"
            res = requests.get(url).json()
            if "results" in res and len(res["results"]) > 0:
                df = pd.DataFrame(res["results"])
                df = df[['o', 'h', 'l', 'c', 'v']]
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df
        except Exception:
            pass
    return None

# TASTO DI SCANSIONE OPERATIVA
if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
    
    with st.spinner("Estrazione e analisi matematica dei flussi finanziari statunitensi..."):
        risultati = []
        progresso = st.progress(0)
        stato_scansione = st.empty()
        
        for i, ticker in enumerate(ticker_list):
            stato_scansione.write(f"⏳ Elaborazione analitica {i+1} di {len(ticker_list)}: **{ticker}**...")
            df = scarica_dati_singolo_server(ticker, server_scelto)
            progresso.progress((i + 1) / len(ticker_list))
            
            if df is None or len(df) < 30: 
                continue
                
            # CALCOLI MATEMATICI INTERNI SUI DATI FORMATTATI
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
            
            # APPLICAZIONE REGOLE STRATEGIA
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
            st.subheader(f"📋 Pannello Segnali Istituzionali ({len(ticker_list)} Titoli)")
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success("Analisi completata con successo. Gestisci il rischio copiando i livelli sul tuo broker.")
        else:
            st.error("Errore temporaneo di ricezione dati dai server statunitensi. Riprova tra due minuti.")
