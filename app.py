import streamlit as st
import pandas as pd
from database import load_data, save_entry, get_unique_drinks

# 1. Seiten-Konfiguration
st.set_page_config(
    page_title="Tasting Cloud Pro", 
    page_icon="🍻", 
    layout="wide"
)

# Styling für die Buttons und Metrics
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.write("Echtzeit-Bewertungen & Bestenliste")
st.markdown("---")

# 2. Sidebar für das User-Profil
with st.sidebar:
    st.header("Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    st.divider()
    st.info("Gib deinen Namen ein, um eigene Bewertungen abzugeben.")

# 3. Hauptbereich mit zwei Spalten
col1, col2 = st.columns([1, 2], gap="large")

# --- LINKE SPALTE: EINGABE ---
with col1:
    if user:
        st.subheader("Neuer Eintrag")
        existing_drinks = get_unique_drinks()
        
        with st.form("rating_form", clear_on_submit=True):
            drink_selection = st.selectbox(
                "Bekanntes Getränk wählen:", 
                options=["-- Neu eintragen --"] + existing_drinks
            )
            
            new_drink_name = st.text_input("Oder neuen Namen tippen:", placeholder="z.B. Augustiner Hell")
            
            if new_drink_name.strip():
                final_drink = new_drink_name.strip()
            elif drink_selection != "-- Neu eintragen --":
                final_drink = drink_selection
            else:
                final_drink = None

            rating = st.select_slider(
                "Bewertung (1-10)", 
                options=list(range(1, 11)), 
                value=5
            )
            
            comment = st.text_area("Dein Fazit", placeholder="Wie schmeckt's?")
            
            submitted = st.form_submit_button("In die Cloud speichern")
            
            if submitted:
                if final_drink:
                    try:
                        save_entry(user, final_drink, rating, comment)
                        st.success(f"Gespeichert!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte Getränkenamen angeben.")
    else:
        st.warning("👈 Bitte gib links deinen Namen ein.")
        st.info("Die Live-Statistik rechts ist für alle Besucher öffentlich.")

# --- RECHTE SPALTE: AUSWERTUNG ---
with col2:
    st.subheader("🏆 Tasting Highlights")
    raw_data = load_data()
    
    if raw_data:
        # Daten in ein sauberes Format bringen
        processed_list = []
        for row in raw_data:
            profiles_data = row.get("Profiles")
            tester_name = profiles_data.get("name", "Unbekannt") if profiles_data else "Unbekannt"
            processed_list.append({
                "Tester": tester_name,
                "Getränk": row.get("drink_aName", "Unbenannt"),
                "Punkte": row.get("rating", 0),
                "Fazit": row.get("remark", "")
            })
        
        df = pd.DataFrame(processed_list)

        # 1. Top 3 Metriken (Hall of Fame)
        if not df.empty:
            avg_df = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
            
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                if len(avg_df) >= 1:
                    st.metric("🥇 Platz 1", avg_df.iloc[0]["Getränk"], f"{avg_df.iloc[0]['Punkte']:.1f} Pkt")
            with h_col2:
                if len(avg_df) >= 2:
                    st.metric("🥈 Platz 2", avg_df.iloc[1]["Getränk"], f"{avg_df.iloc[1]['Punkte']:.1f} Pkt")
            with h_col3:
                if len(avg_df) >= 3:
                    st.metric("🥉 Platz 3", avg_df.iloc[2]["Getränk"], f"{avg_df.iloc[2]['Punkte']:.1f} Pkt")
        
        st.divider()

        # 2. Tabs für Details
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "🎖️ Leaderboard", "📋 Alle Einträge"])
        
        with tab1:
            st.write("### Durchschnitt pro Getränk")
            if not df.empty:
                chart_data = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False)
                st.bar_chart(chart_data)
            
        with tab2:
            st.write("### Wer testet am fleißigsten?")
            leaderboard = df["Tester"].value_counts().reset_index()
            leaderboard.columns = ["Name", "Anzahl Tests"]
            # Wir zeigen eine schicke Tabelle mit Index (Platzierung)
            leaderboard.index += 1
            st.table(leaderboard)
                
        with tab3:
            # Sortiert nach den neuesten Einträgen (dafür wäre ein Timestamp in DB gut)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    else:
        st.info("Noch keine Einträge vorhanden. Sei der Erste!")

st.divider()
st.caption("Besser als Fab4Minds Frontend")