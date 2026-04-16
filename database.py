import os
from supabase import create_client, Client
import pandas as pd

# Verbindung zu Supabase (Wird aus den Streamlit Secrets geladen)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_user_id(name):
    """Sucht User (case-insensitive) oder legt ihn neu an."""
    clean_name = name.strip()
    # ilike sorgt dafür, dass "Lili" und "lili" gleich behandelt werden
    result = supabase.table("Profiles").select("id").ilike("name", clean_name).execute()
    
    if result.data:
        return result.data[0]["id"]
    else:
        # Neu anlegen, falls der Name noch nie existierte
        new_user = supabase.table("Profiles").insert({"name": clean_name}).execute()
        return new_user.data[0]["id"]

def get_unique_drinks():
    """Holt alle bereits existierenden Getränkenamen für das Dropdown."""
    try:
        result = supabase.table("Ratings").select("drink_aName").execute()
        if result.data:
            drinks = [row["drink_aName"] for row in result.data]
            return sorted(list(set(drinks)))
    except Exception:
        return []
    return []

def upload_image(file):
    """Lädt ein Bild hoch und gibt den URL-String zurück."""
    # Eindeutigen Dateinamen generieren
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"pic_{timestamp}_{file.name}"
    
    # Datei in den Bucket 'tasting-pics' schieben
    supabase.storage.from_("tasting-pics").upload(
        path=file_name,
        file=file.getvalue(),
        file_options={"content-type": file.type}
    )
    
    # Die öffentliche URL abrufen
    res = supabase.storage.from_("tasting-pics").get_public_url(file_name)
    
    # WICHTIG: Sicherstellen, dass wir nur den String der URL zurückgeben
    if hasattr(res, 'public_url'):
        return res.public_url
    return str(res)

def save_entry(user_name, drink_name, rating, remark, image_url=None):
    """Speichert eine neue Bewertung in der Tabelle 'Ratings'."""
    user_id = get_user_id(user_name)
    data = {
        "user_id": user_id,
        "drink_aName": drink_name,
        "rating": rating,
        "remark": remark,
        "image_url": image_url
    }
    supabase.table("Ratings").insert(data).execute()

def load_data():
    """Lädt alle Bewertungen und verknüpft sie mit den Namen aus 'Profiles'."""
    # Wir laden alle Spalten aus Ratings und nur das Feld 'name' aus Profiles
    result = supabase.table("Ratings").select("*, Profiles(name)").execute()
    return result.data