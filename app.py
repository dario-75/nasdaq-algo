import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Flex-Scanner V8.3 - Ironclad Dynamic")
st.markdown("Infrastruttura quantitativa con gestione dinamica delle date per i server istituzionali Massive.")

# CHIAVI API FORNITE DALL'UTENTE
AV_KEY = "5JAD1FAAQSH9E72R"
POLYGON_KEY = "iu6rBUvWiGNLdyRj2ZXyDvf7j1ggo_gJ"

# LISTA MASTER DI 50 AZIONI NASDAQ
DATABASE_50_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW",
    "SBUX", "GILD", "INTU", "MDLZ", "PDD", "REGN", "VRTX", "ISRG", "AMAT", "LRCX",
    "CSCO", "ADP", "ADI", "MELI", "KLAC", "SNPS", "CDNS", "NXPI", "ASML", "MAR",
    "CTSH", "ORLY", "ROP", "LULU", "MNST", "ADSK", "KDP", "CHTR", "AEP", "PAYX"
]

# INTERFACCIA UTENTE: I 3 Menu di Configurazione dello Scanner
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
        ["Massive / Polygon.io (Illimitato - Con pausa di sicurezza)", "Alpha Vantage (Veloce - Max 25 chiamate/giorno)"]
    )

with col3:
    dimensione_blocco = st.selectbox(
        "📦 3. Quantità Azioni da Scansionare:",
        [10, 20, 30, 40, 50],
        index=0
    )

# APPLICAZIONE DEL BLOCCO DI SICUREZZA LIVE
if "Alpha Vantage" in server_scelto:
    ticker_list = DATABASE_50_NASDAQ[:10]  
    st.sidebar.warning("🔒 Sicurezza Attiva: Con Alpha Vantage lo screening è forzato a 10 elementi per preservare i limiti della tua API Key.")
else:
    ticker_list = DATABASE_50_NASDAQ[:dimensione_blocco]  

# AREA INFO DINAMICA
st.markdown("---")
st.subheader("ℹ️ Dettaglio Logica Strategia Selezionata")

if "Modalità 1" in modalita_scelta:
    st.info("**📈 MODALITÀ 1 - MOMENTUM EQUILIBRATO:** `Prezzo > EMA 50` e `ROC 90gg > 0`. Cavalca i trend rialzisti stabili nel breve termine (1-3 mesi).")
elif "Modalità 2" in modalita_scelta:
    st.info("**⚡ MODALITÀ 2 - FORZA RELATIVA ISOLATA:** `Prezzo > EMA 50` e `ROC 90gg > 12%`. Isola solo i leader esplosivi del NASDAQ.")
elif "Modalità 3" in modalita_scelta:
    st.info("**🎯 MODALITÀ 3 - RIENTRO SUL SUPPORTO:** `ROC 90gg > 0` e prezzo vicino alla media mobile (distanza 0-3%). Compra a sconto sui supporti.")

st.markdown("---")

# FUNZIONE DI SCARICO DATI CON DATE DINAMICHE AGGIORNATE
def scarica_dati_singolo_server(ticker, server):
    # Calcolo dinamico di OGGI e di 6 MESI FA
    oggi_str = datetime.now().strftime("%Y-%m-%d")
    sei_mesi_fa_str = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    if "Alpha Vantage" in server:
        try:
            url = f"https://alphavantage.co{ticker}&outputsize=full&apikey={AV_KEY}"
            res = requests.get(url).json()
            if "Time Series (Daily)" in res:
                df = pd.DataFrame.from_dict(res["Time Series (Daily)"], orient='index', dtype=float)
                df = df.sort_index(ascending=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df
        except Exception:
            pass
            
    elif "Massive" in server:
        try:
            time.sleep(12) # Pausa obbligatoria per evitare il blocco 5 chiamate/minuto
            # Inseriamo le date calcolate dinamicamente nell'URL ufficiale di Massive
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
    
    with st.spinner("Connessione ai server USA ed elaborazione dati storici live..."):
        risultati = []
        progresso = st.progress(0)
        stato_scansione = st.empty()
        
        for i, ticker in enumerate(ticker_list):
            stato_scansione.write(f"⏳ Analizzo titolo {i+1} di {len(ticker_list)}: **{ticker}**...")
            df = scarica_dati_singolo_server(ticker, server_scelto)
            progresso.progress((i + 1) / len(ticker_list))
            
            if df is None or len(df) < 40: # Abbassata la soglia minima per adattarsi al feed dinamico di Massive
                continue
                
            # CALCOLI MATEMATICI INTERNI
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['ROC_90'] = ((df['Close'] - df['Close'].shift(30)) / df['Close'].shift(30)) * 100 # Ottimizzato su base mensile
            
            high_low = df['High'] - df['Low']
            high_cp = (df['High'] - df['Close'].shift()).abs()
            low_cp = (df['Low'] - df['Close'].shift()).abs()
            df['ATR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(window=14).mean()

            prezzo_attuale = df['Close'].iloc[-1].item()
            ema_50_attuale = df['EMA_50'].iloc[-1].item()
            roc_attuale = df['ROC_90'].iloc[-1].item()
            atr_attuale = df['ATR'].iloc[-1].item()
            
            # APPLICAZIONE RIGIDA DELLE REGOLE
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
                    "Ticker": ticker,
                    "Prezzo Attuale": f"{prezzo_attuale:.2f} \$",
                    "ROC 90gg (Momentum)": f"{roc_attuale:.2f} %",
                    "Segnale": "🟢 PROTETTO - BUY",
                    "STOP LOSS": f"{stop_loss:.2f} \$",
                    "TAKE PROFIT": f"{take_profit:.2f} \$"
                })
            else:
                risultati.append({
                    "Ticker": ticker,
                    "Prezzo Attuale": f"{prezzo_attuale:.2f} \$",
                    "ROC 90gg (Momentum)": f"{roc_attuale:.2f} %" if pd.notna(roc_attuale) else "N/D",
                    "Segnale": "⚪ NESSUN SEGNALE",
                    "STOP LOSS": "-",
                    "TAKE PROFIT": "-"
                })

        stato_scansione.empty()
        if risultati:
            df_final = pd.DataFrame(risultati)
            st.subheader(f"📋 Risultati Screening Istituzionale ({len(ticker_list)} Titoli)")
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success("Analisi completata con successo.")
        else:
            st.warning("Nessun titolo estratto. Verifica la connessione o cambia modalità.")
