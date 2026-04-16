import streamlit as st
import pandas as pd
from database import load_data, save_entry, get_unique_drinks, upload_image

# 1. Seiten-Konfiguration
st.set_page_config(
    page_title="Tasting Cloud Pro 📸", 
    page_icon="🍻", 
    layout="wide"
)

# Styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.write("Echtzeit-Bewertungen mit Foto-Upload & Leaderboard")
st.markdown("---")

# 2. Sidebar
with st.sidebar:
    st.header("Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    st.divider()
    st.info("Logge dich ein, um eigene Bewertungen abzugeben.")

# 3. Hauptbereich
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
            
            new_drink_name = st.text_input("Oder neuer Name:", placeholder="z.B. Tegernseer")
            
            # Logik für den Namen
            if new_drink_name.strip():
                final_drink = new_drink_name.strip()
            elif drink_selection != "-- Neu eintragen --":
                final_drink = drink_selection
            else:
                final_drink = None

            # Foto-Upload
            uploaded_file = st.file_uploader("Foto machen/hochladen", type=["jpg", "jpeg", "png"])
            
            rating = st.select_slider("Bewertung (1-10)", options=list(range(1, 11)), value=5)
            comment = st.text_area("Dein Fazit", placeholder="Wie schmeckt's?")
            
            submitted = st.form_submit_button("In die Cloud speichern 🚀")
            
            if submitted:
                if final_drink:
                    try:
                        image_url = None
                        if uploaded_file:
                            with st.spinner("Bild wird hochgeladen..."):
                                image_url = upload_image(uploaded_file)
                        
                        save_entry(user, final_drink, rating, comment, image_url=image_url)
                        st.success("Erfolgreich gespeichert!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte Namen des Getränks angeben.")
    else:
        st.warning("👈 Bitte gib links deinen Namen ein, um abzustimmen.")

# --- RECHTE SPALTE: AUSWERTUNG ---
with col2:
    st.subheader("🏆 Live-Auswertung")
    raw_data = load_data()
    
    if raw_data:
        processed_list = []
        for row in raw_data:
            profiles_data = row.get("Profiles")
            tester_name = profiles_data.get("name", "Unbekannt") if profiles_data else "Unbekannt"
            processed_list.append({
                "Tester": tester_name,
                "Getränk": row.get("drink_aName", "Unbenannt"),
                "Punkte": row.get("rating", 0),
                "Fazit": row.get("remark", ""),
                "Bild": row.get("image_url", None)
            })
        
        df = pd.DataFrame(processed_list)

        # 1. Top 3 Metriken
        if not df.empty:
            avg_df = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                if len(avg_df) >= 1: st.metric("🥇 Platz 1", avg_df.iloc[0]["Getränk"], f"{avg_df.iloc[0]['Punkte']:.1f} Pkt")
            with h_col2:
                if len(avg_df) >= 2: st.metric("🥈 Platz 2", avg_df.iloc[1]["Getränk"], f"{avg_df.iloc[1]['Punkte']:.1f} Pkt")
            with h_col3:
                if len(avg_df) >= 3: st.metric("🥉 Platz 3", avg_df.iloc[2]["Getränk"], f"{avg_df.iloc[2]['Punkte']:.1f} Pkt")
        
        st.divider()

        # 2. Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "🎖️ Leaderboard", "📸 Fotowall"])
        
        with tab1:
            st.write("### Durchschnittsbewertung")
            st.bar_chart(df.groupby("Getränk")["Punkte"].mean())
            
        with tab2:
            st.write("### Wer testet am fleißigsten?")
            leaderboard = df["Tester"].value_counts().reset_index()
            leaderboard.columns = ["Name", "Anzahl Tests"]
            leaderboard.index += 1
            st.table(leaderboard)
                
        with tab3:
            st.write("### Die neuesten Proben")
            for _, r in df.iterrows():
                with st.container():
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        if r["Bild"]:
                            st.image(r["Bild"], use_container_width=True)
                        else:
                            st.info("Kein Bild")
                    with c2:
                        st.write(f"**{r['Tester']}** probierte **{r['Getränk']}**")
                        st.write(f"Bewertung: **{r['Punkte']}/10 ⭐**")
                        st.write(f"*Fazit: {r['Fazit']}*")
                    st.divider()
    else:
        st.info("Noch keine Daten vorhanden.")

st.divider()
st.caption("Besser als Fab4Minds Frontend")