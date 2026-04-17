import streamlit as st
import pandas as pd
import random
import plotly.graph_objects as go
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

# Radar-Chart Funktionen
def create_radar_chart(row_data):
    categories = ['Geschmack', 'Design', 'Preis-Leistung']
    values = [row_data.get('taste', 5), row_data.get('design', 5), row_data.get('vibe', 5)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(255, 75, 75, 0.3)',
        line_color='#ff4b4b'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#444")),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False,
        height=250, margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

def create_comparison_radar(df, drink_a, drink_b):
    categories = ['Geschmack', 'Design', 'Preis-Leistung']
    stats_a = df[df['Getränk'] == drink_a][['taste', 'design', 'vibe']].mean()
    stats_b = df[df['Getränk'] == drink_b][['taste', 'design', 'vibe']].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[stats_a['taste'], stats_a['design'], stats_a['vibe'], stats_a['taste']],
        theta=categories + [categories[0]], fill='toself', name=drink_a, line_color='#ff4b4b'
    ))
    fig.add_trace(go.Scatterpolar(
        r=[stats_b['taste'], stats_b['design'], stats_b['vibe'], stats_b['taste']],
        theta=categories + [categories[0]], fill='toself', name=drink_b, line_color='#00f2ff'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#444")),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=380
    )
    return fig

# --- Sidebar ---
with st.sidebar:
    st.header("👤 Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    
    if user:
        st.divider()
        if st.button("❌ Letzten Eintrag löschen"):
            if delete_last_entry(user):
                st.warning("Eintrag gelöscht!")
                st.rerun()

    st.divider()
    st.header("🔮 Das Orakel")
    if st.button("Was soll ich trinken?"):
        raw_data = load_data()
        if raw_data:
            all_drinks = list(set([r["drink_aName"] for r in raw_data]))
            st.success(f"Probier mal: **{random.choice(all_drinks)}**")

    st.divider()
    st.header("💾 Export")
    raw_export = load_data()
    if raw_export:
        export_df = pd.DataFrame([{
            "Tester": r.get("Profiles", {}).get("name"),
            "Getränk": r.get("drink_aName"),
            "Rating": r.get("rating"),
            "Geschmack": r.get("taste"),
            "Design": r.get("design"),
            "Preis-Leistung": r.get("vibe")
        } for r in raw_export])
        st.download_button("📥 CSV Download", export_df.to_csv(index=False).encode('utf-8'), "tasting.csv", "text/csv")

# --- Main ---
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    if user:
        st.subheader("📝 Bewertung")
        existing_drinks = get_unique_drinks()
        with st.form("rating_form", clear_on_submit=True):
            drink_selection = st.selectbox("Getränk:", options=["-- Neu --"] + existing_drinks)
            new_name = st.text_input("Oder Name:")
            final_drink = new_name.strip() if new_name.strip() else (drink_selection if drink_selection != "-- Neu --" else None)
            uploaded_file = st.file_uploader("Foto", type=["jpg", "png"])
            
            st.write("**Deep Analysis:**")
            c_taste = st.slider("👅 Geschmack", 1, 10, 5)
            c_design = st.slider("🎨 Design", 1, 10, 5)
            c_price = st.slider("💰 Preis-Leistung", 1, 10, 5)
            
            rating = st.select_slider("⭐ Gesamtnote", options=list(range(1, 11)), value=5)
            comment = st.text_area("Fazit")
            
            if st.form_submit_button("Speichern 🚀"):
                if final_drink:
                    img_url = upload_image(uploaded_file) if uploaded_file else None
                    res = save_entry(user, final_drink, rating, comment, c_design, c_taste, c_price, img_url)
                    st.success("Gespeichert!" if res == "inserted" else "Aktualisiert!")
                    st.rerun()
    else:
        st.warning("👈 Gib links deinen Namen ein.")

with col2:
    raw_data = load_data()
    if raw_data:
        processed = [{"id": r.get("id"), "Tester": r.get("Profiles", {}).get("name"), "Getränk": r.get("drink_aName"), "Punkte": r.get("rating"), "taste": r.get("taste"), "design": r.get("design"), "vibe": r.get("vibe"), "Fazit": r.get("remark"), "Bild": r.get("image_url")} for r in raw_data]
        df = pd.DataFrame(processed)

        # Leaderboard Tabs etc.
        t1, t2, t3, t4 = st.tabs(["🎖️ Leaderboard", "📸 Fotowall", "📊 Stats", "⚔️ Duell"])
        
        with t1:
            st.table(df["Tester"].value_counts().reset_index())
        
        with t2:
            for r in reversed(processed):
                c_a, c_b, c_c = st.columns([1, 1, 1.5])
                with c_a: 
                    if r["Bild"]: st.image(r["Bild"])
                with c_b: st.plotly_chart(create_radar_chart(r), use_container_width=True, key=f"r_{r['id']}")
                with c_c:
                    st.write(f"**{r['Tester']}** testete **{r['Getränk']}**")
                    st.subheader(f"{r['Punkte']}/10 ⭐")
                    st.caption(r["Fazit"])
                st.divider()

        with t4:
            all_d = sorted(df["Getränk"].unique())
            if len(all_d) >= 2:
                d1 = st.selectbox("Getränk 1", all_d, index=0)
                d2 = st.selectbox("Getränk 2", all_d, index=1)
                st.plotly_chart(create_comparison_radar(df, d1, d2), use_container_width=True)
    else:
        st.info("Noch keine Daten.")
st.caption("Besser als Fab4Minds Frontend")