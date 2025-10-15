"""
⚽ FOGNA - Applicazione Web PROTETTA con Livelli di Accesso
- ADMIN: Può vedere tutto e modificare
- UTENTE: Può solo vedere le statistiche
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re
import os

# Configurazione della pagina (DEVE essere PRIMA di tutto!)
st.set_page_config(
    page_title="⚽ FOGNA - Statistiche Calcio",
    page_icon="⚽",
    layout="wide"
)

# Disabilita PyArrow COMPLETAMENTE (causa errori su Python 3.14)
import sys
sys.modules['pyarrow'] = None  # Blocca import di pyarrow
os.environ["PYARROW_IGNORE_TIMEZONE"] = "1"

# CONFIGURAZIONE CREDENZIALI - FUNZIONA LOCALE + WEB
# Rileva automaticamente se sei in locale o online

# Verifica se è ONLINE guardando se esiste secrets E l'hostname
try:
    # Se riesce a leggere secrets, è ONLINE
    ADMIN_PASSWORD = st.secrets["passwords"]["admin"]
    UTENTE_PASSWORD = st.secrets["passwords"]["utente"]
    MODE = "🌐 ONLINE"
    IS_LOCAL = False
except:
    # Se fallisce, è LOCALE
    ADMIN_PASSWORD = "fogna"
    UTENTE_PASSWORD = "vinceremo"
    MODE = "🏠 LOCALE"
    IS_LOCAL = True

CREDENZIALI = {
    "admin": {
        "password": ADMIN_PASSWORD,
        "ruolo": "Amministratore",
        "icona": "👑"
    },
    "utente": {
        "password": UTENTE_PASSWORD,
        "ruolo": "Utente",
        "icona": "👤"
    }
}

def verifica_login():
    """Gestisce il sistema di login con livelli di accesso"""
    
    # Inizializza lo stato della sessione
    if "autenticato" not in st.session_state:
        st.session_state.autenticato = False
        st.session_state.tipo_utente = None
        st.session_state.nome_utente = None
    
    # Se già autenticato, permetti l'accesso
    if st.session_state.autenticato:
        return True
    
    # Altrimenti mostra schermata di login
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>⚽ FOGNA</h1>
        <h3>Sistema Statistiche Calcistiche</h3>
        <p style='color: #666;'>🔒 Accesso Riservato</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Form di login centrato
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        
        tipo_login = st.radio(
            "Tipo di accesso:",
            ["👑 Amministratore", "👤 Utente"],
            horizontal=True
        )
        
        # Determina tipo utente
        tipo = "admin" if "Amministratore" in tipo_login else "utente"
        
        password_inserita = st.text_input(
            "Password:",
            type="password",
            placeholder="Inserisci la password...",
            key="password_input"
        )
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔓 ACCEDI", type="primary", use_container_width=True):
                if password_inserita == CREDENZIALI[tipo]["password"]:
                    st.session_state.autenticato = True
                    st.session_state.tipo_utente = tipo
                    st.session_state.nome_utente = CREDENZIALI[tipo]["ruolo"]
                    st.success(f"✅ Benvenuto {CREDENZIALI[tipo]['icona']} {CREDENZIALI[tipo]['ruolo']}!")
                    st.rerun()
                else:
                    st.error("❌ Password errata! Riprova.")
        
        st.markdown("---")
        st.info("""
        💡 **Livelli di accesso:**
        - 👑 **Amministratore**: Accesso completo (visualizza + modifica)
        - 👤 **Utente**: Solo visualizzazione statistiche
        """)
    
    return False

# VERIFICA LOGIN
if not verifica_login():
    st.stop()

# ============================================================================
# APP PRINCIPALE
# ============================================================================

# Header con info utente, indicatore ambiente e logout
col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    icona = CREDENZIALI[st.session_state.tipo_utente]["icona"]
    ruolo = st.session_state.nome_utente
    st.markdown(f"### {icona} Benvenuto, {ruolo}")
with col2:
    # Indicatore GRANDE e visibile locale/web
    if MODE == "🏠 LOCALE":
        st.info(f"**{MODE}** - Ambiente di sviluppo", icon="🏠")
    else:
        st.success(f"**{MODE}** - Ambiente di produzione", icon="🌐")
with col3:
    st.write("")  # Spazio
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.autenticato = False
        st.session_state.tipo_utente = None
        st.session_state.nome_utente = None
        st.rerun()

st.markdown("---")

# Inizializza il database
@st.cache_resource
def init_database():
    """Inizializza il database SQLite"""
    conn = sqlite3.connect('football_stats.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            div TEXT,
            date TEXT,
            time TEXT,
            home_team TEXT,
            away_team TEXT,
            fthg INTEGER,
            ftag INTEGER,
            ftr TEXT,
            hthg INTEGER,
            htag INTEGER,
            htr TEXT,
            hs INTEGER,
            as_team INTEGER,
            hst INTEGER,
            ast INTEGER,
            hf INTEGER,
            af INTEGER,
            hc INTEGER,
            ac INTEGER,
            hy INTEGER,
            ay INTEGER,
            hr INTEGER,
            ar INTEGER,
            season TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def extract_season_from_filename(filename):
    """Estrae automaticamente la stagione dal nome file"""
    season_pattern = r'(\d{4})-(\d{4})'
    match = re.search(season_pattern, filename)
    
    if match:
        year1 = int(match.group(1))
        year2 = int(match.group(2))
        
        if year2 == year1 + 1:
            return f"{year1}-{year2}"
    return None

conn = init_database()

# Sidebar - Menu dinamico in base al tipo utente
st.sidebar.markdown("# 🏠 Menu")

# Determina pagine disponibili in base al ruolo
if st.session_state.tipo_utente == "admin":
    # ADMIN vede tutto
    pagine_disponibili = [
        "🏠 Home", 
        "📤 Carica File", 
        "🏆 BEST Teams", 
        "📊 Classifiche", 
        "🗂️ Gestione Dati"
    ]
else:
    # UTENTE vede solo statistiche
    pagine_disponibili = [
        "🏠 Home", 
        "🏆 BEST Teams", 
        "📊 Classifiche"
    ]

page = st.sidebar.radio("Vai a:", pagine_disponibili)

st.sidebar.markdown("---")
icona_stato = CREDENZIALI[st.session_state.tipo_utente]["icona"]
st.sidebar.success(f"{icona_stato} {st.session_state.nome_utente}")

# Mostra avviso per utenti normali
if st.session_state.tipo_utente == "utente":
    st.sidebar.info("👤 **Modalità Solo Lettura**\n\nPuoi visualizzare le statistiche ma non modificare i dati.")

# ============================================================================
# PAGINE
# ============================================================================

# HOME PAGE
if page == "🏠 Home":
    st.markdown("# ⚽ FOGNA - Statistiche Calcio")
    st.markdown("### Benvenuto nel Sistema di Statistiche Calcistiche!")
    
    cursor = conn.cursor()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COUNT(*) FROM matches")
        total = cursor.fetchone()[0]
        st.metric("Partite Totali", total)
    
    with col2:
        cursor.execute("SELECT COUNT(DISTINCT season) FROM matches WHERE season IS NOT NULL")
        seasons = cursor.fetchone()[0]
        st.metric("Stagioni", seasons)
    
    with col3:
        cursor.execute("SELECT COUNT(DISTINCT div) FROM matches")
        leagues = cursor.fetchone()[0]
        st.metric("Campionati", leagues)
    
    with col4:
        cursor.execute("SELECT COUNT(DISTINCT home_team) FROM matches")
        teams = cursor.fetchone()[0]
        st.metric("Squadre", teams)
    
    st.markdown("---")
    st.markdown("### 📅 Stagioni Disponibili")
    cursor.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
    seasons_list = [s[0] for s in cursor.fetchall()]
    
    if seasons_list:
        st.success(f"🎯 Stagioni: {', '.join(seasons_list)}")
    else:
        st.warning("⚠️ Nessuna stagione caricata.")
        if st.session_state.tipo_utente == "admin":
            st.info("💡 Vai su 'Carica File' per aggiungere dati!")

elif page == "📤 Carica File":
    if st.session_state.tipo_utente != "admin":
        st.error("⛔ Accesso negato! Solo gli amministratori possono caricare file.")
        st.stop()
    
    st.markdown("# 📤 Carica File Excel")
    
    st.info("""
    **Istruzioni:**
    1. Seleziona il file Excel
    2. La stagione viene riconosciuta automaticamente dal nome
    3. Formato nome: all-euro-data-YYYY-YYYY.xlsx
    """)
    
    uploaded_file = st.file_uploader("Scegli file Excel", type=['xlsx', 'xls'])
    
    if uploaded_file:
        st.success(f"✅ File: {uploaded_file.name}")
        
        season = extract_season_from_filename(uploaded_file.name)
        if season:
            st.info(f"🎯 Stagione: **{season}**")
        else:
            st.warning("⚠️ Stagione non riconosciuta")
        
        load_type = st.radio(
            "Tipo caricamento:",
            ["normal", "overwrite"],
            format_func=lambda x: "📥 Carica Normalmente" if x == "normal" else "🔄 Sovrascrivi Stagione"
        )
        
        if st.button("🚀 CARICA FILE", type="primary"):
            try:
                with st.spinner("Caricamento..."):
                    excel_file = pd.ExcelFile(uploaded_file)
                    all_data = []
                    
                    for sheet in excel_file.sheet_names:
                        df = pd.read_excel(uploaded_file, sheet_name=sheet)
                        
                        if 'Div' not in df.columns:
                            df['Div'] = sheet
                        
                        df['Season'] = season
                        
                        col_map = {
                            'HomeTeam': 'home_team', 'AwayTeam': 'away_team',
                            'FTHG': 'fthg', 'FTAG': 'ftag', 'FTR': 'ftr',
                            'HTHG': 'hthg', 'HTAG': 'htag', 'HTR': 'htr',
                            'HS': 'hs', 'AS': 'as_team', 'HST': 'hst', 'AST': 'ast',
                            'HF': 'hf', 'AF': 'af', 'HC': 'hc', 'AC': 'ac',
                            'HY': 'hy', 'AY': 'ay', 'HR': 'hr', 'AR': 'ar',
                            'Season': 'season', 'Div': 'div', 'Date': 'date', 'Time': 'time'
                        }
                        
                        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                        df = df.dropna(subset=['home_team', 'away_team'])
                        
                        if len(df) > 0:
                            all_data.append(df)
                    
                    if all_data:
                        combined = pd.concat(all_data, ignore_index=True)
                        
                        if load_type == "overwrite" and season:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM matches WHERE season = ?", (season,))
                            conn.commit()
                        
                        combined.to_sql('matches', conn, if_exists='append', index=False)
                        conn.commit()
                        
                        st.success(f"✅ Caricati {len(combined)} risultati!")
                        st.balloons()
                    else:
                        st.error("Nessun dato valido trovato")
                        
            except Exception as e:
                st.error(f"Errore: {str(e)}")

# BEST TEAMS
elif page == "🏆 BEST Teams":
    st.markdown("# 🏆 BEST Teams")
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
    all_seasons = [s[0] for s in cursor.fetchall()]
    
    if not all_seasons:
        st.warning("⚠️ Nessuna stagione disponibile")
        st.stop()
    
    # Layout migliorato: tutto su una riga
    col1, col2, col3 = st.columns([3, 1, 1.5])
    
    with col1:
        selected_seasons = st.multiselect(
            "📅 Seleziona Stagioni:", 
            all_seasons, 
            default=[all_seasons[0]],  # Solo l'ultima stagione selezionata di default
            help="Seleziona una o più stagioni da analizzare"
        )
    
    with col2:
        threshold = st.number_input("🎯 Soglia %:", 0, 100, 65, 1, help="Percentuale minima di vittorie")
    
    with col3:
        st.write("")  # Spazio per allineare
        mostra = st.button("🏆 MOSTRA BEST TEAMS", type="primary", use_container_width=True)
    
    # Indicatore stagioni selezionate
    if selected_seasons:
        st.info(f"📊 Analizzando **{len(selected_seasons)}** stagione/i: {', '.join(selected_seasons)}")
    else:
        st.warning("⚠️ Seleziona almeno una stagione!")
    
    if selected_seasons and mostra:
        seasons_str = "','".join(selected_seasons)
        query = f"""
        WITH all_matches AS (
          SELECT home_team AS team, div AS league, season,
                 CASE WHEN fthg > ftag THEN 1 ELSE 0 END AS win,
                 CASE WHEN fthg = ftag THEN 1 ELSE 0 END AS draw,
                 CASE WHEN fthg < ftag THEN 1 ELSE 0 END AS loss
          FROM matches WHERE season IN ('{seasons_str}')
          UNION ALL
          SELECT away_team AS team, div AS league, season,
                 CASE WHEN ftag > fthg THEN 1 ELSE 0 END AS win,
                 CASE WHEN ftag = fthg THEN 1 ELSE 0 END AS draw,
                 CASE WHEN ftag < fthg THEN 1 ELSE 0 END AS loss
          FROM matches WHERE season IN ('{seasons_str}')
        )
        SELECT team, league, season,
               COUNT(*) AS played,
               SUM(win) AS wins,
               SUM(draw) AS draws,
               SUM(loss) AS losses,
               ROUND(CAST(SUM(win) AS FLOAT)/COUNT(*)*100, 1) AS win_pct,
               SUM(win)*3 + SUM(draw) AS points
        FROM all_matches
        GROUP BY team, league, season
        HAVING win_pct >= {threshold}
        ORDER BY win_pct DESC, points DESC, played DESC, team ASC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if len(df) > 0:
            st.success(f"🎯 Trovate {len(df)} squadre con percentuale >= {threshold}%")
            
            df.insert(0, 'Pos', range(1, len(df) + 1))
            df = df[["Pos","team","league","season","played","wins","draws","losses","win_pct","points"]]
            df.columns = ['Pos', 'Squadra', 'Campionato', 'Stagione', 'P', 'V', 'N', 'P2', 'V%', 'Pts']
            
            # Mostra dataframe (senza column_config per evitare pyarrow)
            st.dataframe(df, hide_index=True)
        else:
            st.warning(f"Nessuna squadra con % >= {threshold}%")

# CLASSIFICHE
elif page == "📊 Classifiche":
    st.markdown("# 📊 Classifiche Campionati")
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT div FROM matches ORDER BY div")
    leagues = [l[0] for l in cursor.fetchall()]
    
    if leagues:
        selected_league = st.selectbox("🏟️ Campionato:", leagues)
        
        cursor.execute(f"SELECT DISTINCT season FROM matches WHERE div = ? ORDER BY season DESC", (selected_league,))
        seasons = [s[0] for s in cursor.fetchall()]
        
        if seasons:
            selected_season = st.selectbox("📅 Stagione:", seasons)
            
            if st.button("📊 MOSTRA CLASSIFICA", type="primary"):
                query = f"""
                    SELECT 
                        home_team as team,
                        COUNT(*) as played,
                        SUM(CASE WHEN fthg > ftag THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN fthg = ftag THEN 1 ELSE 0 END) as draws,
                        SUM(CASE WHEN fthg < ftag THEN 1 ELSE 0 END) as losses,
                        SUM(fthg) as gf,
                        SUM(ftag) as ga,
                        SUM(fthg) - SUM(ftag) as gd,
                        SUM(CASE WHEN fthg > ftag THEN 3 WHEN fthg = ftag THEN 1 ELSE 0 END) as points
                    FROM matches
                    WHERE div = ? AND season = ?
                    GROUP BY home_team
                    ORDER BY points DESC, gd DESC
                """
                
                df = pd.read_sql_query(query, conn, params=(selected_league, selected_season))
                
                if len(df) > 0:
                    df.insert(0, 'Pos', range(1, len(df) + 1))
                    df.columns = ['Pos', 'Squadra', 'P', 'V', 'N', 'P2', 'GF', 'GS', 'DR', 'Pts']
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nessun dato")
    else:
        st.warning("Nessun campionato disponibile")

# GESTIONE DATI (SOLO ADMIN)
elif page == "🗂️ Gestione Dati":
    if st.session_state.tipo_utente != "admin":
        st.error("⛔ Accesso negato! Solo gli amministratori possono gestire i dati.")
        st.stop()
    
    st.markdown("# 🗂️ Gestione Dati")
    
    tab1, tab2, tab3 = st.tabs(["📁 File", "📥 Esporta", "🗑️ Elimina"])
    
    with tab1:
        st.markdown("### 📁 File Caricati")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT season, COUNT(*) as num
            FROM matches
            WHERE season IS NOT NULL
            GROUP BY season
            ORDER BY season DESC
        """)
        
        data = cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=['Stagione', 'Partite'])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"📊 {len(data)} stagioni | {sum([d[1] for d in data])} partite")
        else:
            st.warning("Nessun file")
    
    with tab2:
        st.markdown("### 📥 Esporta Dati")
        if st.button("📥 ESPORTA CSV", type="primary"):
            df = pd.read_sql_query("SELECT * FROM matches", conn)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Scarica CSV",
                csv,
                f"fogna_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    with tab3:
        st.markdown("### 🗑️ Elimina Dati")
        st.warning("⚠️ Operazione irreversibile!")
        
        cursor.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
        seasons = [s[0] for s in cursor.fetchall()]
        
        if seasons:
            season_del = st.selectbox("Stagione da eliminare:", seasons)
            if st.button("🗑️ ELIMINA", type="secondary"):
                cursor.execute("DELETE FROM matches WHERE season = ?", (season_del,))
                conn.commit()
                st.success(f"✅ Stagione {season_del} eliminata!")
                st.rerun()

st.markdown("---")
icona_footer = CREDENZIALI[st.session_state.tipo_utente]["icona"]
st.markdown(f"<div style='text-align: center; color: #666;'>⚽ FOGNA - {icona_footer} {st.session_state.nome_utente} 🔒</div>", unsafe_allow_html=True)

