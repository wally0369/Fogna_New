import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import re

st.set_page_config(page_title="FOGNA - Statistiche Calcio", layout="wide")

CREDENZIALI = {
    "admin": {"password": "fogna", "ruolo": "Amministratore"},
    "utente": {"password": "vinceremo", "ruolo": "Utente"},
}

def verifica_login() -> bool:
    if "autenticato" not in st.session_state:
        st.session_state.autenticato = False
        st.session_state.tipo_utente = None
        st.session_state.nome_utente = None

    if st.session_state.autenticato:
        return True

    st.title("FOGNA - Statistiche Calcio")

    with st.form("login_form", clear_on_submit=True):
        tipo = st.radio("Tipo di accesso", ["Amministratore", "Utente"], horizontal=True, key="tipo_accesso")
        pwd = st.text_input("Password", type="password", key="pwd_input")
        submitted = st.form_submit_button("Accedi")

    if submitted:
        tipo_key = "admin" if tipo == "Amministratore" else "utente"
        if pwd.strip() == CREDENZIALI[tipo_key]["password"]:
            st.session_state.autenticato = True
            st.session_state.tipo_utente = tipo_key
            st.session_state.nome_utente = CREDENZIALI[tipo_key]["ruolo"]
            st.rerun()
        else:
            st.error("Password errata")

    return False

@st.cache_resource
def init_database():
    conn = sqlite3.connect("football_stats.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
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
    """)
    conn.commit()
    return conn

def extract_season_from_filename(filename: str):
    m = re.search(r"(\d{4})-(\d{4})", filename)
    if not m:
        return None
    y1, y2 = int(m.group(1)), int(m.group(2))
    return f"{y1}-{y2}" if y2 == y1 + 1 else None

def show_home_page(conn):
    st.header("Home")
    cur = conn.cursor()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cur.execute("SELECT COUNT(*) FROM matches")
        st.metric("Partite Totali", cur.fetchone()[0])
    with c2:
        cur.execute("SELECT COUNT(DISTINCT season) FROM matches WHERE season IS NOT NULL")
        st.metric("Stagioni", cur.fetchone()[0])
    with c3:
        cur.execute("SELECT COUNT(DISTINCT div) FROM matches")
        st.metric("Campionati", cur.fetchone()[0])
    with c4:
        cur.execute("SELECT COUNT(DISTINCT home_team) FROM matches")
        st.metric("Squadre", cur.fetchone()[0])
    st.markdown("---")
    cur.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
    seasons = [s[0] for s in cur.fetchall()]
    if seasons:
        st.success("Stagioni: " + ", ".join(seasons))
    else:
        st.info("Nessuna stagione caricata. Usa 'Carica File' per aggiungere dati.")

def show_upload_page(conn):
    if st.session_state.tipo_utente != "admin":
        st.error("Accesso negato (solo amministratori).")
        st.stop()
    st.header("Carica File")
    st.info("Usa file Excel: all-euro-data-YYYY-YYYY.xlsx")
    uploaded = st.file_uploader("Seleziona file Excel", type=["xlsx", "xls"])
    if not uploaded:
        return
    st.success(f"File selezionato: {uploaded.name}")
    season = extract_season_from_filename(uploaded.name)
    if season:
        st.info(f"Stagione rilevata: {season}")
    else:
        st.warning("Stagione non riconosciuta dal nome file")
    load_type = st.radio("Tipo caricamento", ["normal", "overwrite"],
                         format_func=lambda x: "Aggiungi" if x == "normal" else "Sovrascrivi stagione")
    if st.button("Carica", type="primary"):
        with st.spinner("Elaborazione..."):
            try:
                xls = pd.ExcelFile(uploaded)
                all_data = []
                for sheet in xls.sheet_names:
                    df = pd.read_excel(uploaded, sheet_name=sheet)
                    if "Div" not in df.columns:
                        df["Div"] = sheet
                    df["Season"] = season
                    col_map = {
                        "HomeTeam": "home_team", "AwayTeam": "away_team",
                        "FTHG": "fthg", "FTAG": "ftag", "FTR": "ftr",
                        "HTHG": "hthg", "HTAG": "htag", "HTR": "htr",
                        "HS": "hs", "AS": "as_team", "HST": "hst", "AST": "ast",
                        "HF": "hf", "AF": "af", "HC": "hc", "AC": "ac",
                        "HY": "hy", "AY": "ay", "HR": "hr", "AR": "ar",
                        "Season": "season", "Div": "div", "Date": "date", "Time": "time",
                    }
                    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                    allowed = [
                        "div","date","time","home_team","away_team",
                        "fthg","ftag","ftr","hthg","htag","htr",
                        "hs","as_team","hst","ast","hf","af","hc","ac",
                        "hy","ay","hr","ar","season",
                    ]
                    present = [c for c in allowed if c in df.columns]
                    df = df[present]
                    df = df.dropna(subset=["home_team","away_team"])
                    if len(df) > 0:
                        all_data.append(df)
                if not all_data:
                    st.error("Nessun dato valido trovato.")
                    return
                combined = pd.concat(all_data, ignore_index=True)
                cur = conn.cursor()
                if load_type == "overwrite" and season:
                    cur.execute("DELETE FROM matches WHERE season = ?", (season,))
                    conn.commit()
                combined.to_sql("matches", conn, if_exists="append", index=False)
                conn.commit()
                st.success(f"Caricate {len(combined)} righe.")
            except Exception as e:
                st.error(f"Errore: {e}")

def show_best_teams_page(conn):
    st.header("BEST Teams")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
    seasons = [s[0] for s in cur.fetchall()]
    if not seasons:
        st.info("Nessuna stagione disponibile")
        return

    selected_seasons = st.multiselect("Stagioni", seasons, default=seasons)
    threshold = st.number_input("Soglia % vittorie", min_value=0, max_value=100, value=65, step=1)

    if st.button("Mostra", type="primary") and selected_seasons:
        seasons_str = ",".join(f"'{s}'" for s in selected_seasons)
        query = f"""
        WITH all_matches AS (
          SELECT home_team AS team, div AS league, season,
                 CASE WHEN fthg > ftag THEN 1 ELSE 0 END AS win,
                 CASE WHEN fthg = ftag THEN 1 ELSE 0 END AS draw,
                 CASE WHEN fthg < ftag THEN 1 ELSE 0 END AS loss
          FROM matches WHERE season IN ({seasons_str})
          UNION ALL
          SELECT away_team AS team, div AS league, season,
                 CASE WHEN ftag > fthg THEN 1 ELSE 0 END AS win,
                 CASE WHEN ftag = fthg THEN 1 ELSE 0 END AS draw,
                 CASE WHEN ftag < fthg THEN 1 ELSE 0 END AS loss
          FROM matches WHERE season IN ({seasons_str})
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
        if df.empty:
            st.info("Nessun risultato.")
            return
        df.insert(0, "Pos", range(1, len(df) + 1))
        df = df[["Pos","team","league","season","played","wins","draws","losses","win_pct","points"]]
        df.columns = ["Pos","Squadra","Campionato","Stagione","P","V","N","P2","V%","Pts"]
        st.dataframe(
    df,
    hide_index=True,
    use_container_width=False,  # evita l’allargamento automatico
    column_order=["Pos","Squadra","Campionato","Stagione","P","V","N","P2","V%","Pts"],
    column_config={
        "Pts": st.column_config.NumberColumn("Pts", width="small"),
        "V%":  st.column_config.NumberColumn("V%",  format="%.1f", width="small"),
        "P":   st.column_config.NumberColumn("P",   width="small"),
        "P2":  st.column_config.NumberColumn("P2",  width="small"),
    },
)
def show_standings_page(conn):
    st.header("Classifiche")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT div FROM matches ORDER BY div")
    leagues = [l[0] for l in cur.fetchall()]
    if not leagues:
        st.info("Nessun campionato disponibile")
        return

    selected_league = st.selectbox("Campionato", leagues)
    cur.execute("SELECT DISTINCT season FROM matches WHERE div = ? ORDER BY season DESC", (selected_league,))
    seasons = [s[0] for s in cur.fetchall()]
    if not seasons:
        st.info("Nessuna stagione per questo campionato")
        return

    selected_season = st.selectbox("Stagione", seasons)

    if st.button("Mostra Classifica", type="primary"):
        query = """
        WITH all_matches AS (
          SELECT home_team AS team, div, season,
                 CASE WHEN fthg > ftag THEN 1 ELSE 0 END AS win,
                 CASE WHEN fthg = ftag THEN 1 ELSE 0 END AS draw,
                 CASE WHEN fthg < ftag THEN 1 ELSE 0 END AS loss,
                 fthg AS gf, ftag AS ga
          FROM matches WHERE div = ? AND season = ?
          UNION ALL
          SELECT away_team AS team, div, season,
                 CASE WHEN ftag > fthg THEN 1 ELSE 0 END AS win,
                 CASE WHEN ftag = fthg THEN 1 ELSE 0 END AS draw,
                 CASE WHEN ftag < fthg THEN 1 ELSE 0 END AS loss,
                 ftag AS gf, fthg AS ga
          FROM matches WHERE div = ? AND season = ?
        )
        SELECT team,
               COUNT(*) AS played,
               SUM(win) AS wins,
               SUM(draw) AS draws,
               SUM(loss) AS losses,
               SUM(gf) AS gf,
               SUM(ga) AS ga,
               SUM(gf) - SUM(ga) AS gd,
               SUM(win)*3 + SUM(draw) AS points
        FROM all_matches
        GROUP BY team
        ORDER BY points DESC, gd DESC, gf DESC, team ASC
        """
        df = pd.read_sql_query(query, conn, params=(selected_league, selected_season, selected_league, selected_season))
        if df.empty:
            st.info("Nessun dato.")
            return
        df.insert(0, "Pos", range(1, len(df) + 1))
        df = df[["Pos","Squadra","P","V","N","P2","GF","GS","DR","Pts"]]
st.table(
    df.style.set_properties(
        subset=["P","V","N","P2","GF","GS","DR","Pts"],
        **{"text-align": "center", "width": "70px"}
    ).set_properties(
        subset=["Squadra"],
        **{"width": "220px"}
    )
)
def show_data_management_page(conn):
    if st.session_state.tipo_utente != "admin":
        st.error("Accesso negato (solo amministratori).")
        st.stop()
    st.header("Gestione Dati")
    tab1, tab2, tab3 = st.tabs(["File","Esporta","Elimina"])
    with tab1:
        cur = conn.cursor()
        cur.execute("""
            SELECT season, COUNT(*) as num
            FROM matches
            WHERE season IS NOT NULL
            GROUP BY season
            ORDER BY season DESC
        """)
        data = cur.fetchall()
        if data:
            df = pd.DataFrame(data, columns=["Stagione","Partite"])
            st.table(
    df.style.set_properties(subset=["Pts"], **{"width": "60px"})
)
        else:
            st.info("Nessun file caricato.")
    with tab2:
        if st.button("Esporta CSV", type="primary"):
            df = pd.read_sql_query("SELECT * FROM matches", conn)
            csv = df.to_csv(index=False)
            st.download_button("Scarica CSV", csv, f"fogna_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    with tab3:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
        seasons = [s[0] for s in cur.fetchall()]
        if not seasons:
            st.info("Nessuna stagione da eliminare")
        else:
            season = st.selectbox("Stagione da eliminare", seasons)
            if st.button("Elimina", type="secondary"):
                cur.execute("DELETE FROM matches WHERE season = ?", (season,))
                conn.commit()
                st.success(f"Eliminata stagione {season}")
                st.experimental_rerun()

if not verifica_login():
    st.stop()

conn = init_database()

st.sidebar.markdown(f"Utente: {st.session_state.nome_utente}")
pages = ["Home", "Carica File", "BEST Teams", "Classifiche"]
if st.session_state.tipo_utente == "admin":
    pages.append("Gestione Dati")
page = st.sidebar.radio("Vai a", pages)

if page == "Home":
    show_home_page(conn)
if page == "Carica File":
    show_upload_page(conn)
if page == "BEST Teams":
    show_best_teams_page(conn)
if page == "Classifiche":
    show_standings_page(conn)
if page == "Gestione Dati":
    show_data_management_page(conn)

st.markdown("---")
st.caption("FOGNA - Statistiche Calcio")
