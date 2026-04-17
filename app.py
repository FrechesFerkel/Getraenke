import streamlit as st
import pandas as pd
import random
from database import load_data, save_entry, get_unique_drinks, upload_image

# 1. Seiten-Konfiguration
st.set_page_config(page_title="Tasting Cloud Pro", page_icon="🍻", layout="wide")

# Styling für Badges und Buttons
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .user-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; background: #444; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.markdown("---")

# 2. Sidebar mit Orakel
with st.sidebar:
    st.header("👤 Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    
    st.divider()
    st.header("🔮 Das Orakel")
    if st.button("Was soll ich trinken?"):
        raw_data = load_data()
        if raw_data:
            all_drinks = list(set([r["drink_aName"] for r in raw_data]))
            recommendation = random.choice(all_drinks)
            st.success(f"Das Schicksal sagt: \n**{recommendation}**!")
        else:
            st.info("Noch keine Daten für Empfehlungen.")

# 3. Hauptbereich
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    if user:
        st.subheader("📝 Neuer Eintrag")
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
                    img_url = upload_image(uploaded_file) if uploaded_file else None
                    save_entry(user, final_drink, rating, comment, image_url=img_url)
                    st.success("Gespeichert!")
                    st.rerun()
                else:
                    st.warning("Name fehlt!")
    else:
        st.warning("👈 Namen eingeben, um zu starten.")

with col2:
    raw_data = load_data()
    if raw_data:
        # Daten-Aufbereitung
        processed_list = [{
            "Tester": r.get("Profiles", {}).get("name", "Unbekannt"),
            "Getränk": r.get("drink_aName", "Unbenannt"),
            "Punkte": r.get("rating", 0),
            "Fazit": r.get("remark", ""),
            "Bild": r.get("image_url", None)
        } for r in raw_data]
        df = pd.DataFrame(processed_list)

        # --- SEKTION: SOMMELIER-ANALYSE (NR. 1) ---
        st.subheader("🧐 Sommelier-Check")
        avg_per_user = df.groupby("Tester")["Punkte"].mean()
        
        if user in avg_per_user:
            my_avg = avg_per_user[user]
            if my_avg > 8: status = "😇 Die Gute-Laune-Maschine (Sehr spendabel)"
            elif my_avg < 4: status = "🧐 Der Mecker-Gourmet (Sehr streng)"
            else: status = "⚖️ Der faire Genießer"
            st.info(f"**Dein Vibe:** {status} (Schnitt: {my_avg:.1f} Pkt)")

        # Metriken (Top 3)
        avg_drink = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
        m1, m2, m3 = st.columns(3)
        if len(avg_drink) > 0: m1.metric("🥇 Platz 1", avg_drink.iloc[0]["Getränk"], f"{avg_drink.iloc[0]['Punkte']:.1f}")
        if len(avg_drink) > 1: m2.metric("🥈 Platz 2", avg_drink.iloc[1]["Getränk"], f"{avg_drink.iloc[1]['Punkte']:.1f}")
        if len(avg_drink) > 2: m3.metric("🥉 Platz 3", avg_drink.iloc[2]["Getränk"], f"{avg_drink.iloc[2]['Punkte']:.1f}")

        st.divider()
        t1, t2, t3 = st.tabs(["🎖️ Leaderboard", "📸 Fotowall", "📊 Alle Stats"])
        
        with t1:
            st.write("### Wer rockt das Tasting?")
            counts = df["Tester"].value_counts().reset_index()
            counts.columns = ["Name", "Tests"]
            
            # Badges vergeben
            def add_badges(row):
                name = row["Name"]
                badge_str = name
                if row.name == 0: badge_str += " 👑" # Meiste Tests
                if df[df["Tester"] == name]["Bild"].count() > 0: badge_str += " 📸" # Hat Bilder gemacht
                return badge_str

            counts["Name"] = counts.apply(add_badges, axis=1)
            st.table(counts)
        
        with t2:
            for r in processed_list:
                with st.container():
                    c_img, c_txt = st.columns([1, 2])
                    if r["Bild"]: c_img.image(r["Bild"], use_container_width=True)
                    c_txt.write(f"**{r['Tester']}** testete **{r['Getränk']}**")
                    c_txt.subheader(f"{r['Punkte']}/10 ⭐")
                    if r["Fazit"]: st.caption(f"💬 {r['Fazit']}")
                    st.divider()

        with t3:
            st.bar_chart(df.groupby("Getränk")["Punkte"].mean())
    else:
        st.info("Noch keine Daten.")
st.caption("Besser als Fab4Minds Frontend")