import streamlit as st
import pandas as pd
from database import load_data, save_entry, get_unique_drinks

# 1. Seiten-Konfiguration
st.set_page_config(
    page_title="Tasting Cloud Pro", 
    page_icon="🍻", 
    layout="wide"
)

# Styling für ein schöneres Interface
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🍻 Team Tasting Cloud")
st.write("Bewertungen werden sicher in der Supabase-Cloud gespeichert.")
st.markdown("---")

# 2. Sidebar für das User-Profil
with st.sidebar:
    st.header("Profil")
    user = st.text_input("Dein Name", placeholder="z.B. Benjamin")
    st.divider()
    st.info("Dein Name wird in der 'Profiles'-Tabelle gespeichert und mit deinen Ratings verknüpft.")

# 3. Hauptbereich
if user:
    col1, col2 = st.columns([1, 2], gap="large")

    # --- LINKE SPALTE: EINGABE ---
    with col1:
        st.subheader("Neuer Eintrag")
        
        # Aktuelle Getränkeliste aus der DB laden für Vorschläge
        existing_drinks = get_unique_drinks()
        
        with st.form("rating_form", clear_on_submit=True):
            # Auswahl aus Liste
            drink_selection = st.selectbox(
                "Bekanntes Getränk wählen:", 
                options=["-- Neu eintragen --"] + existing_drinks
            )
            
            # Manuelle Eingabe
            new_drink_name = st.text_input("Oder neuen Namen tippen:", placeholder="z.B. Augustiner Hell")
            
            # Bestimmen, welcher Name genutzt wird
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
                        st.success(f"Eintrag für '{final_drink}' wurde gespeichert!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {e}")
                else:
                    st.warning("Bitte gib einen Namen für das Getränk an.")

    # --- RECHTE SPALTE: AUSWERTUNG ---
    with col2:
        st.subheader("Live-Auswertung")
        raw_data = load_data()
        
        if raw_data:
            processed_list = []
            for row in raw_data:
                # Sicherer Zugriff auf die verknüpfte Profiles-Tabelle
                profiles_data = row.get("Profiles")
                
                if profiles_data is not None:
                    tester_name = profiles_data.get("name", "Unbekannt")
                else:
                    tester_name = "Unbekannt"
                
                processed_list.append({
                    "Tester": tester_name,
                    "Getränk": row.get("drink_aName", "Unbenannt"),
                    "Punkte": row.get("rating", 0),
                    "Fazit": row.get("remark", "")
                })
            
            df = pd.DataFrame(processed_list)
            
            tab1, tab2 = st.tabs(["📊 Statistik", "📋 Alle Einträge"])
            
            with tab1:
                st.write("### Durchschnitt pro Getränk")
                if not df.empty:
                    avg_ratings = df.groupby("Getränk")["Punkte"].mean().sort_values(ascending=False)
                    st.bar_chart(avg_ratings)
                else:
                    st.write("Noch keine Daten für Statistik.")
                
            with tab2:
                st.dataframe(
                    df, 
                    use_container_width=True, 
                    hide_index=True
                )
        else:
            st.info("Noch keine Einträge in der Cloud vorhanden.")

else:
    st.warning("👈 Bitte gib links in der Sidebar deinen Namen ein, um zu starten.")

st.divider()
st.caption("Besser als Fab4Minds Frontend")