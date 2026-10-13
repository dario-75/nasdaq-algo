import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Full-Scanner V10.0 - Nasdaq-100 Engine")
st.markdown("Infrastruttura quantitativa professionale estesa all'intero paniere delle 100 più grandi aziende del NASDAQ.")

# CHIAVI API FORNITE DALL'UTENTE
AV_KEY = "5JAD1FAAQSH9E72R"
POLYGON_KEY = "iu6rBUvWiGNLdyRj2ZXyDvf7j1ggo_gJ"

# LISTA COMPLETA DEI 100 COMPONENTI PRINCIPALI DEL NASDAQ-100 (Ordinati per capitalizzazione)
DATABASE_100_NASDAQ = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
    "AMD", "INTC", "QCOM", "ADBE", "TXN", "AMGN", "MU", "HON", "BKNG", "PANW",
    "SBUX", "GILD", "INTU", "MDLZ", "PDD", "REGN", "VRTX", "ISRG", "AMAT", "LRCX",
    "CSCO", "ADP", "ADI", "MELI", "KLAC", "SNPS", "CDNS", "NXPI", "ASML", "MAR",
    "CTSH", "ORLY", "ROP", "LULU", "MNST", "ADSK", "KDP", "CHTR", "AEP", "PAYX",
    "PANW", "MRVL", "ORLY", "ODFL", "PCAR", "GILD", "MCHP", "AZN", "EXC", "LULU",
    "CPRT", "CSX", "CTAS", "DLTR", "DOCU", "DXCM", "EA", "FAST", "FTNT", "IDXX",
    "ILMN", "KHC", "MDB", "MELI", "MNST", "MRNA", "OKTA", "TEAM", "VRSK", "WDAY",
    "XEL", "ZM", "ALGN", "ANSS", "BIIB", "DDOG", "FANG", "GEHC", "ROST", "SIRI",
    "SPLK", "VRSN", "WBA", "WBD", "BKR", "CDW", "CEG", "COR", "TTD", "ON"
]

# DETTAGLI TOOLTIP PER L'ICONA INFO
HELP_MODALITA = (
    "ℹ️ LOGICA DELLE STRATEGIE QUANTITATIVE:\n\n"
    "• Modalità 1 (Momentum Equilibrato): Prezzo sopra la media mobile a 50 giorni (EMA 50) e rendimento a 3 mesi positivo (ROC > 0).\n\n"
    "• Modalità 2 (Forza Relativa Isolata): Isola solo i leader esplosivi che corrono a una velocità superiore al +12% netto negli ultimi 3 mesi.\n\n"
    "• Modalità 3 (Rientro sul Supporto): Trova titoli in forte trend a 3 mesi che hanno appena subito un piccolo ritracciamento, posizionandosi vicini alla loro EMA 50 (distanza 0-3%)."
)

# INTERFACCIA UTENTE
col1, col2 = st.columns(2)

with col1:
    modalita_scelta = st.selectbox(
        "🛡️ 1. Seleziona la Modalità Algoritmica:",
        [
            "Modalità 1: Momentum Equilibrato (Trend Following)",
            "Modalità 2: Forza Relativa Isolata (Alpha Seeker)",
            "Modalità 3: Rientro sul Supporto (Pullback)"
        ],
        help=HELP_MODALITA
    )

with col2:
    server_scelto = st.selectbox(
        "🔌 2. Seleziona il Server da Interrogare:",
        ["Massive / Polygon.io (Illimitato - Con pausa di sicurezza)", "Alpha Vantage (Veloce - Max 25 chiamate/giorno)"]
    )

st.markdown("---")
st.subheader("📦 Configurazione Universo Azionario")

scelta_universo = st.radio(
    "Scegli come inserire le azioni da scansionare (un'opzione esclude l'altra):",
    ["Usa i Blocchi preimpostati (da 5 a 100 azioni)", "Inserimento Manuale Singolo (digita i ticker a mano)"]
)

ticker_list = []

if scelta_universo == "Usa i Blocchi preimpostati (da 5 a 100 azioni)":
    # Slider esteso fino a un massimo di 100 titoli
    dimensione_blocco = st.slider(
        "Quantità Azioni del Blocco da scansionare:",
        min_value=5,
        max_value=100,
        value=5,
        step=5
    )
    ticker_list = DATABASE_100_NASDAQ[:dimensione_blocco]
else:
    ticker_manuali_input = st.text_input(
        "✍️ Digita i simboli delle azioni separati da una virgola (es: PLTR, SMCI, TSLA):", 
        value="PLTR, SMCI"
    )
    ticker_list = [t.strip().upper() for t in ticker_manuali_input.split(",") if t.strip()]

st.markdown("---")

# CONTROLLO AVVISO PREVENTIVO DI SICUREZZA
blocco_tasto_scansione = False

if "Alpha Vantage" in server_scelto and len(ticker_list) > 15:
    st.error(f"🚨 AZIONE BLOCCATA PREVENTIVAMENTE: Con il server Alpha Vantage hai selezionato {len(ticker_list)} azioni. Superando il limite di sicurezza di 15 titoli complessivi, il pulsante è disattivato per proteggere la tua API Key. Riduci i titoli a meno di 15 o passa al server istituzionale Massive.")
    blocco_tasto_scansione = True
else:
    tempo_stimato_minuti = (len(ticker_list) * 12) / 60 if "Massive" in server_scelto else 0
    if tempo_stimato_minuti > 0:
        st.warning(f"⏳ NOTA DI TEMPO: Lo screening su {len(ticker_list)} titoli richiederà circa {tempo_stimato_minuti:.1f} minuti su server Massive (causa pause anti-ban). Mantieni attiva questa schermata sul telefono.")
    st.write(f"🔍 **Universo in scansione attuale:** {len(ticker_list)} azioni del paniere NASDAQ-100.")
    st.caption(f"Titoli inclusi: {', '.join(ticker_list)}")

# FUNZIONE DI SCARICO DATI REALI USA
def scarica_dati_singolo_server(ticker, server):
    oggi_str = datetime.now().strftime("%Y-%m-%d")
    sei_mesi_fa_str = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

    if "Alpha Vantage" in server:
        try:
            time.sleep(12) 
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
            time.sleep(12) 
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

# GESTIONE PULSANTE DI SCANSIONE LIVE
if blocco_tasto_scansione:
    st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary", disabled=True)
else:
    if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
        
        with st.spinner("Estrazione e analisi matematica dei flussi finanziari del NASDAQ-100..."):
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
                st.error("Nessun dato estratto. Riprova tra qualche istante.")
