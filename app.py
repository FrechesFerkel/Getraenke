import streamlit as st
import pandas as pd
import random
from database import load_data, save_entry, get_unique_drinks, upload_image, delete_last_entry

# 1. Seiten-Konfiguration
st.set_page_config(page_title="Tasting Cloud Pro", page_icon="🍻", layout="wide")

# Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .shame-box { padding: 10px; border: 2px solid #ff4b4b; border-radius: 10px; background-color: #2a0000; color: white; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.markdown("---")

# 2. Sidebar
with st.sidebar:
    st.header("👤 Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    
    if user:
        st.divider()
        if st.button("❌ Letzten Eintrag löschen"):
            if delete_last_entry(user):
                st.warning("Eintrag wurde entfernt!")
                st.rerun()
            else:
                st.error("Kein Eintrag zum Löschen gefunden.")
    
    st.divider()
    st.header("🔮 Das Orakel")
    if st.button("Was soll ich trinken?"):
        raw_data = load_data()
        if raw_data:
            all_drinks = list(set([r["drink_aName"] for r in raw_data]))
            recommendation = random.choice(all_drinks)
            st.success(f"Das Schicksal sagt: \n**{recommendation}**!")
        else:
            st.info("Noch keine Daten.")

    st.divider()
    st.header("🔍 Fotowall Filter")
    raw_for_filter = load_data()
    tester_list = sorted(list(set([r.get("Profiles", {}).get("name", "Unbekannt") for r in raw_for_filter]))) if raw_for_filter else []
    filter_user = st.selectbox("Nur von Tester:", options=["Alle"] + tester_list)

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
        processed_list = [{
            "Tester": r.get("Profiles", {}).get("name", "Unbekannt"),
            "Getränk": r.get("drink_aName", "Unbenannt"),
            "Punkte": r.get("rating", 0),
            "Fazit": r.get("remark", ""),
            "Bild": r.get("image_url", None)
        } for r in raw_data]
        df = pd.DataFrame(processed_list)

        # Sommelier-Analyse
        avg_per_user = df.groupby("Tester")["Punkte"].mean()
        if user in avg_per_user:
            my_avg = avg_per_user[user]
            status = "😇 Die Gute-Laune-Maschine" if my_avg > 8 else ("🧐 Der Mecker-Gourmet" if my_avg < 4 else "⚖️ Der faire Genießer")
            st.info(f"**Dein Vibe:** {status} (Schnitt: {my_avg:.1f} Pkt)")

        # Highlights & Hall of Shame
        avg_drink = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
        m1, m2, m3 = st.columns(3)
        if len(avg_drink) > 0: m1.metric("🥇 Platz 1", avg_drink.iloc[0]["Getränk"], f"{avg_drink.iloc[0]['Punkte']:.1f}")
        if len(avg_drink) > 1: m2.metric("🥈 Platz 2", avg_drink.iloc[1]["Getränk"], f"{avg_drink.iloc[1]['Punkte']:.1f}")
        
        if len(avg_drink) >= 1:
            shame_drink = avg_drink.iloc[-1]
            with m3:
                st.markdown(f"<div class='shame-box'>💀 Hall of Shame<br><b>{shame_drink['Getränk']}</b><br>{shame_drink['Punkte']:.1f} Pkt</div>", unsafe_allow_html=True)

        st.divider()
        t1, t2, t3 = st.tabs(["🎖️ Leaderboard", "📸 Fotowall", "📊 Alle Stats"])
        
        with t1:
            counts = df["Tester"].value_counts().reset_index()
            counts.columns = ["Name", "Tests"]; counts.index += 1
            st.table(counts)
        
        with t2:
            display_list = processed_list if filter_user == "Alle" else [r for r in processed_list if r["Tester"] == filter_user]
            for r in reversed(display_list): # Neueste zuerst anzeigen
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