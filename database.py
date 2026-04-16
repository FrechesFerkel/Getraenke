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
    result = supabase.table("Profiles").select("id").ilike("name", clean_name).execute()
    
    if result.data:
        return result.data[0]["id"]
    else:
        new_user = supabase.table("Profiles").insert({"name": clean_name}).execute()
        return new_user.data[0]["id"]

def get_unique_drinks():
    """Holt alle bereits existierenden Getränkenamen."""
    result = supabase.table("Ratings").select("drink_aName").execute()
    if result.data:
        drinks = [row["drink_aName"] for row in result.data]
        return sorted(list(set(drinks)))
    return []

def upload_image(file):
    """Lädt ein Bild hoch und gibt die URL zurück."""
    # Wir nehmen den Dateinamen des Uploads als Basis
    file_name = f"pic_{file.name}"
    
    supabase.storage.from_("tasting-pics").upload(
        path=file_name,
        file=file.getvalue(),
        file_options={"content-type": "image/jpeg"}
    )
    
    url_res = supabase.storage.from_("tasting-pics").get_public_url(file_name)
    return url_res

def save_entry(user_name, drink_name, rating, remark, image_url=None):
    """Speichert eine neue Bewertung."""
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
    """Lädt alle Bewertungen OHNE Sortierung nach created_at."""
    # Hier wurde das .order() entfernt, um den Fehler zu beheben
    result = supabase.table("Ratings").select("*, Profiles(name)").execute()
    return result.data