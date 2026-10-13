import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# Configurazione della pagina della Web App
st.set_page_config(layout="wide")
st.title("📊 NASDAQ Algo Scanner V8.1 - Professional Engine")
st.markdown("Infrastruttura quantitativa d'élite con descrizioni didattiche e sorgenti dati istituzionali statunitensi.")

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
,
        index=0
    )

# AREA INFO DINAMICA: PANNELLO DETTAGLIO MODALITÀ SELEZIONATA
st.markdown("---")
st.subheader("ℹ️ Dettaglio Logica Strategia Selezionata")

if "Modalità 1" in modalita_scelta:
    st.info(
        "**📈 MODALITÀ 1 - MOMENTUM EQUILIBRATO (Cavalca il Trend):**\n\n"
        "* **Logica Matematica:** Filtra le azioni che hanno il prezzo dell'ultimo giorno superiore alla Media Mobile Esponenziale a 50 giorni (`Prezzo > EMA 50`) e un rendimento a 3 mesi positivo (`ROC 90gg > 0`).\n"
        "* **Obiettivo Finanziario:** Comprare i titoli tecnologici che sono già in una fase rialzista chiara, sfruttando la continuazione del trend per le successive settimane.\n"
        "* **Profilo di Rischio:** Bilanciato. È la strategia quantitativa più utilizzata per l'orizzonte temporale 1-3 mesi."
    )
elif "Modalità 2" in modalita_scelta:
    st.info(
        "**⚡ MODALITÀ 2 - FORZA RELATIVA ISOLATA (Caccia ai Leader):**\n\n"
        "* **Logica Matematica:** Applica una selezione durissima. Il titolo deve essere sopra la sua `EMA 50` e deve registrare un Momentum esponenziale negli ultimi 3 mesi superiore al **+12.0% netto**.\n"
        "* **Obiettivo Finanziario:** Isolare esclusivamente i 'campioni' del NASDAQ, ovvero quelle poche aziende che attirano i massimi volumi di capitali da parte dei grandi fondi d'investimento americani.\n"
        "* **Profilo di Rischio:** Medio-Alto. Trova meno segnali, ma seleziona azioni con una spinta esplosiva che spesso corrono anche quando il mercato generale rallenta."
    )
elif "Modalità 3" in modalita_scelta:
    st.info(
        "**🎯 MODALITÀ 3 - RIENTRO SUL SUPPORTO (Comprare a Sconto):**\n\n"
        "* **Logica Matematica:** Cerca titoli che hanno un trend di fondo saldamente rialzista a 3 mesi (`ROC 90gg > 0`), ma che nelle ultime sessioni hanno subito un ritracciamento, posizionandosi vicinissimi alla loro media mobile (distanza tra `Prezzo` ed `EMA 50` compresa tra **0% e 3%**).\n"
        "* **Obiettivo Finanziario:** Evitare l'errore psicologico di comprare sui massimi storici. L'algoritmo attende un momento di temporanea debolezza ('respiro' del prezzo) per farti entrare vicino a un supporto tecnico importante.\n"
        "* **Profilo di Rischio:** Conservativo. Ottimizza il rapporto rischio/rendimento perché posiziona l'ingresso molto vicino al livello di Stop Loss statistico."
    )

# Estrazione dinamica del blocco di azioni
ticker_list = DATABASE_50_NASDAQ[:dimensione_blocco]
st.markdown("---")

# FUNZIONE DI SCARICO DATI
def scarica_dati_singolo_server(ticker, server):
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
            time.sleep(12) # Pausa obbligatoria anti-ban per Massive Free (5 chiamate/minuto max)
            url = f"https://polygon.io{ticker}/range/1/day/2025-01-01/2026-12-31?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_KEY}"
            res = requests.get(url).json()
            if "results" in res:
                df = pd.DataFrame(res["results"])
                df = df[['o', 'h', 'l', 'c', 'v']]
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                return df
        except Exception:
            pass
    return None

# TASTO DI SCANSIONE OPERATIVA
if st.button("🔥 AVVIA SCANSIONE QUANTITATIVA", type="primary"):
    
    with st.spinner("Analisi quantitativa in corso sui server statunitensi..."):
        risultati = []
        progresso = st.progress(0)
        stato_scansione = st.empty()
        
        for i, ticker in enumerate(ticker_list):
            stato_scansione.write(f"⏳ Analizzo titolo {i+1} di {len(ticker_list)}: **{ticker}**...")
            df = scarica_dati_singolo_server(ticker, server_scelto)
            progresso.progress((i + 1) / len(ticker_list))
            
            if df is None or len(df) < 100:
                continue
                
            # CALCOLI MATEMATICI INTERNI
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
            
            # FILTRI DELLE 3 MODALITÀ
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
            st.subheader("📋 Risultati Screening Istituzionale")
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            st.success("Analisi completata con successo.")
