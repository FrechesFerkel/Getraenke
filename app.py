import streamlit as st
import pandas as pd
from database import load_data, save_entry, get_unique_drinks, upload_image

# 1. Seiten-Konfiguration
st.set_page_config(page_title="Tasting Cloud 📸", page_icon="🍻", layout="wide")

# Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #ff4b4b; color: white; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.markdown("---")

# 2. Sidebar
with st.sidebar:
    st.header("Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")

# 3. Hauptbereich
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    if user:
        st.subheader("Neuer Eintrag")
        existing_drinks = get_unique_drinks()
        
        with st.form("rating_form", clear_on_submit=True):
            drink_selection = st.selectbox("Getränk wählen:", options=["-- Neu eintragen --"] + existing_drinks)
            new_drink_name = st.text_input("Oder Name tippen:")
            
            final_drink = new_drink_name.strip() if new_drink_name.strip() else (drink_selection if drink_selection != "-- Neu eintragen --" else None)
            uploaded_file = st.file_uploader("Foto hochladen", type=["jpg", "jpeg", "png"])
            rating = st.select_slider("Bewertung", options=list(range(1, 11)), value=5)
            comment = st.text_area("Fazit")
            
            if st.form_submit_button("Speichern 🚀"):
                if final_drink:
                    img_url = None
                    if uploaded_file:
                        try:
                            img_url = upload_image(uploaded_file)
                        except Exception as e:
                            st.error(f"Upload-Fehler: {e}")
                    
                    save_entry(user, final_drink, rating, comment, image_url=img_url)
                    st.success("Gespeichert!")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Name fehlt!")
    else:
        st.warning("👈 Namen eingeben.")

with col2:
    st.subheader("🏆 Auswertung")
    raw_data = load_data()
    
    if raw_data:
        processed_list = []
        for row in raw_data:
            prof = row.get("Profiles")
            # Sicherstellen, dass wir einen String für das Bild haben
            img_val = row.get("image_url")
            if img_val and not isinstance(img_val, str):
                img_val = getattr(img_val, 'public_url', None)

            processed_list.append({
                "Tester": prof.get("name", "Unbekannt") if isinstance(prof, dict) else "Unbekannt",
                "Getränk": row.get("drink_aName", "Unbenannt"),
                "Punkte": row.get("rating", 0),
                "Fazit": row.get("remark", ""),
                "Bild": img_val
            })
        
        df = pd.DataFrame(processed_list)

        # Metriken (Top 3)
        if not df.empty:
            avg_df = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
            m1, m2, m3 = st.columns(3)
            if len(avg_df) > 0: m1.metric("🥇 1.", avg_df.iloc[0]["Getränk"], f"{avg_df.iloc[0]['Punkte']:.1f}")
            if len(avg_df) > 1: m2.metric("🥈 2.", avg_df.iloc[1]["Getränk"], f"{avg_df.iloc[1]['Punkte']:.1f}")
            if len(avg_df) > 2: m3.metric("🥉 3.", avg_df.iloc[2]["Getränk"], f"{avg_df.iloc[2]['Punkte']:.1f}")
        
        st.divider()
        t1, t2, t3 = st.tabs(["📊 Charts", "🎖️ Leaderboard", "📸 Fotowall"])
        
        with t1: st.bar_chart(df.groupby("Getränk")["Punkte"].mean())
        with t2:
            lb = df["Tester"].value_counts().reset_index()
            lb.columns = ["Name", "Tests"]; lb.index += 1
            st.table(lb)
        with t3:
            # Neueste zuerst
            for r in processed_list:
                c_img, c_txt = st.columns([1, 2])
                if r["Bild"] and isinstance(r["Bild"], str):
                    c_img.image(r["Bild"], use_container_width=True)
                else:
                    c_img.gray_image = True # Platzhalter-Optik
                    c_img.write(" Kein Foto")
                
                c_txt.write(f"**{r['Tester']}** testete **{r['Getränk']}**")
                c_txt.write(f"Punkte: {r['Punkte']}/10")
                if r["Fazit"]: c_txt.info(r["Fazit"])
                st.divider()
    else:
        st.info("Noch keine Daten.")
st.caption("Besser als Fab4Minds Frontend")