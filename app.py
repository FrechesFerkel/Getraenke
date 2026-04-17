import streamlit as st
import pandas as pd
import random
import plotly.graph_objects as go
# WICHTIG: Hier muss 'has_user_rated_drink' mit importiert werden
from database import load_data, save_entry, get_unique_drinks, upload_image, delete_last_entry, has_user_rated_drink

# 1. Seiten-Konfiguration
st.set_page_config(page_title="Tasting Cloud Pro", page_icon="🍻", layout="wide")

# Styling (Bleibt gleich)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .shame-box { padding: 10px; border: 2px solid #ff4b4b; border-radius: 10px; background-color: #2a0000; color: white; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")

# --- HILFSFUNKTIONEN FÜR CHARTS (Bleiben gleich) ---
def create_radar_chart(row_data):
    categories = ['Geschmack', 'Design']
    values = [row_data.get('taste', 5), row_data.get('design', 5)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself', fillcolor='rgba(255, 75, 75, 0.3)', line_color='#ff4b4b'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#444"), angularaxis=dict(gridcolor="#444")), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=220, margin=dict(l=40, r=40, t=20, b=20))
    return fig

def create_comparison_radar(df, drink_a, drink_b):
    categories = ['Geschmack', 'Design']
    stats_a = df[df['Getränk'] == drink_a][['taste', 'design']].mean()
    stats_b = df[df['Getränk'] == drink_b][['taste', 'design']].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[stats_a['taste'], stats_a['design'], stats_a['taste']], theta=categories + [categories[0]], fill='toself', name=drink_a, line_color='#ff4b4b', fillcolor='rgba(255, 75, 75, 0.2)'))
    fig.add_trace(go.Scatterpolar(r=[stats_b['taste'], stats_b['design'], stats_b['taste']], theta=categories + [categories[0]], fill='toself', name=drink_b, line_color='#00f2ff', fillcolor='rgba(0, 242, 255, 0.2)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#444"), angularaxis=dict(gridcolor="#444")), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=50, r=50, t=40, b=40))
    return fig

# --- 2. SIDEBAR (Alle alten Features inklusive) ---
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
                st.error("Kein Eintrag gefunden.")
    
    st.divider()
    st.header("🔮 Das Orakel")
    if st.button("Was soll ich trinken?"):
        raw_data = load_data()
        if raw_data:
            all_drinks = list(set([r["drink_aName"] for r in raw_data]))
            st.success(f"Das Schicksal sagt: \n**{random.choice(all_drinks)}**!")

    st.divider()
    st.header("💾 Daten-Export")
    raw_export_data = load_data()
    if raw_export_data:
        export_list = [{"Datum": r.get("created_at", ""), "Tester": r.get("Profiles", {}).get("name", "Unbekannt"), "Getränk": r.get("drink_aName", "Unbenannt"), "Gesamt-Rating": r.get("rating", 0), "Geschmack": r.get("taste", 5), "Design": r.get("design", 5), "Fazit": r.get("remark", ""), "Bild-URL": r.get("image_url", "")} for r in raw_export_data]
        export_df = pd.DataFrame(export_list)
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Liste herunterladen", data=csv, file_name=f"tasting_export_{pd.Timestamp.now().strftime('%Y%m%d')}.csv", mime="text/csv")

    st.divider()
    st.header("🔍 Fotowall Filter")
    raw_for_filter = load_data()
    tester_list = sorted(list(set([r.get("Profiles", {}).get("name", "Unbekannt") for r in raw_for_filter]))) if raw_for_filter else []
    filter_user = st.selectbox("Nur von Tester:", options=["Alle"] + tester_list)

# --- 3. HAUPTBEREICH ---
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
            
            st.write("**Deep Analysis (1-10):**")
            c_taste = st.slider("👅 Geschmack", 1, 10, 5)
            c_design = st.slider("🎨 Design/Label", 1, 10, 5)
            rating = st.select_slider("Gesamtnote ⭐", options=list(range(1, 11)), value=5)
            comment = st.text_area("Fazit")
            
            if st.form_submit_button("Speichern 🚀"):
                if final_drink:
                    # --- NEUE DOPPEL-CHECK LOGIK ---
                    if has_user_rated_drink(user, final_drink):
                        st.error(f"🛑 Stop! Du hast **{final_drink}** bereits bewertet. Probiere mal was Neues!")
                    else:
                        img_url = upload_image(uploaded_file) if uploaded_file else None
                        save_entry(user_name=user, drink_name=final_drink, rating=rating, remark=comment, design=c_design, taste=c_taste, image_url=img_url)
                        st.success("Erfolgreich gespeichert!")
                        st.rerun()
                else:
                    st.warning("Bitte gib einen Namen für das Getränk ein.")
    else:
        st.warning("👈 Namen eingeben, um zu starten.")

with col2:
    # (Restlicher Code für Leaderboard, Fotowall, Stats und Duell bleibt exakt wie vorher)
    raw_data = load_data()
    if raw_data:
        processed_list = [{"id": r.get("id"), "Tester": r.get("Profiles", {}).get("name", "Unbekannt"), "Getränk": r.get("drink_aName", "Unbenannt"), "Punkte": r.get("rating", 0), "taste": r.get("taste", 5), "design": r.get("design", 5), "Fazit": r.get("remark", ""), "Bild": r.get("image_url", None)} for r in raw_data]
        df = pd.DataFrame(processed_list)

        avg_per_user = df.groupby("Tester")["Punkte"].mean()
        if user in avg_per_user:
            my_avg = avg_per_user[user]
            status = "😇 Die Gute-Laune-Maschine" if my_avg > 8 else ("🧐 Der Mecker-Gourmet" if my_avg < 4 else "⚖️ Der faire Genießer")
            st.info(f"**Dein Vibe:** {status} (Schnitt: {my_avg:.1f} Pkt)")

        avg_drink = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False).reset_index()
        m1, m2, m3 = st.columns(3)
        if len(avg_drink) > 0: m1.metric("🥇 Platz 1", avg_drink.iloc[0]["Getränk"], f"{avg_drink.iloc[0]['Punkte']:.1f}")
        if len(avg_drink) > 1: m2.metric("🥈 Platz 2", avg_drink.iloc[1]["Getränk"], f"{avg_drink.iloc[1]['Punkte']:.1f}")
        if len(avg_drink) >= 1:
            shame_drink = avg_drink.iloc[-1]
            with m3: st.markdown(f"<div class='shame-box'>💀 Hall of Shame<br><b>{shame_drink['Getränk']}</b><br>{shame_drink['Punkte']:.1f} Pkt</div>", unsafe_allow_html=True)

        st.divider()
        t1, t2, t3, t4 = st.tabs(["🎖️ Leaderboard", "📸 Fotowall", "📊 Stats", "⚔️ Duell"])
        
        with t1:
            counts = df["Tester"].value_counts().reset_index()
            counts.columns = ["Name", "Tests"]
            def add_badges(row):
                name = row["Name"]
                badge_str = name
                if row.name == 0: badge_str += " 👑"
                if df[df["Tester"] == name]["Bild"].count() > 0: badge_str += " 📸"
                if df[df["Tester"] == name]["Punkte"].max() == 10: badge_str += " 🔥"
                return badge_str
            counts["Name"] = counts.apply(add_badges, axis=1)
            st.table(counts)
        
        with t2:
            display_list = processed_list if filter_user == "Alle" else [r for r in processed_list if r["Tester"] == filter_user]
            for r in reversed(display_list):
                with st.container():
                    c_img, c_radar, c_txt = st.columns([1.2, 1.2, 1.5])
                    with c_img:
                        if r["Bild"]: st.image(r["Bild"], use_container_width=True)
                    with c_radar:
                        st.plotly_chart(create_radar_chart(r), use_container_width=True, config={'displayModeBar': False}, key=f"radar_{r['id']}")
                    with c_txt:
                        st.write(f"**{r['Tester']}** testete **{r['Getränk']}**")
                        st.subheader(f"{r['Punkte']}/10 ⭐")
                        if r["Fazit"]: st.caption(f"💬 {r['Fazit']}")
                    st.divider()

        with t3:
            st.bar_chart(df.groupby("Getränk")["Punkte"].mean())

        with t4:
            st.write("### ⚔️ Direktes Duell")
            all_drinks_list = sorted(df["Getränk"].unique())
            if len(all_drinks_list) >= 2:
                c_d1, c_d2 = st.columns(2)
                drink_1 = c_d1.selectbox("Herausforderer 1", all_drinks_list, index=0, key="d1")
                drink_2 = c_d2.selectbox("Herausforderer 2", all_drinks_list, index=1, key="d2")
                if drink_1 != drink_2:
                    st.plotly_chart(create_comparison_radar(df, drink_1, drink_2), use_container_width=True)
                    s1, s2 = df[df['Getränk'] == drink_1]['Punkte'].mean(), df[df['Getränk'] == drink_2]['Punkte'].mean()
                    st.markdown(f"**Punkte-Check:** \n{drink_1}: `{s1:.1f} ⭐`  \n{drink_2}: `{s2:.1f} ⭐`")
                else:
                    st.warning("Bitte zwei verschiedene Getränke wählen!")
            else:
                st.info("Nicht genug Getränke für ein Duell.")
    else:
        st.info("Noch keine Daten.")
st.caption("Besser als Fab4Minds Frontend")