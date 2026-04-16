import os
from supabase import create_client, Client
import pandas as pd

# Verbindung zu Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_user_id(name):
    """Sucht User (case-insensitive) oder legt ihn neu an."""
    clean_name = name.strip()
    # Suche mit ilike (ignoriert Groß-/Kleinschreibung)
    result = supabase.table("Profiles").select("id").ilike("name", clean_name).execute()
    
    if result.data:
        return result.data[0]["id"]
    else:
        # Neu anlegen, falls nicht gefunden
        new_user = supabase.table("Profiles").insert({"name": clean_name}).execute()
        return new_user.data[0]["id"]

def get_unique_drinks():
    """Holt alle bereits existierenden Getränkenamen für das Dropdown."""
    result = supabase.table("Ratings").select("drink_aName").execute()
    if result.data:
        drinks = [row["drink_aName"] for row in result.data]
        return sorted(list(set(drinks)))
    return []

def upload_image(file):
    """Lädt ein Bild in den Supabase Storage 'tasting-pics' hoch."""
    # Zeitstempel für eindeutigen Dateinamen
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"pic_{timestamp}_{file.name}"
    
    # Upload
    supabase.storage.from_("tasting-pics").upload(
        path=file_name,
        file=file.getvalue(),
        file_options={"content-type": "image/jpeg"}
    )
    
    # URL abrufen
    url_res = supabase.storage.from_("tasting-pics").get_public_url(file_name)
    return url_res

def save_entry(user_name, drink_name, rating, remark, image_url=None):
    """Speichert eine neue Bewertung inkl. optionaler Bild-URL."""
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
    """Lädt alle Bewertungen für die Auswertung."""
    # Holt Ratings und verknüpft sie mit der Profiles Tabelle
    result = supabase.table("Ratings").select("*, Profiles(name)").order("created_at", desc=True).execute()
    return result.data