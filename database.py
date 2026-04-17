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
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"pic_{timestamp}_{file.name}"
    
    supabase.storage.from_("tasting-pics").upload(
        path=file_name,
        file=file.getvalue(),
        file_options={"content-type": file.type}
    )
    
    res = supabase.storage.from_("tasting-pics").get_public_url(file_name)
    if hasattr(res, 'public_url'):
        return res.public_url
    return str(res)

def save_entry(user_name, drink_name, rating, remark, design, taste, vibe, image_url=None):
    """Speichert eine neue Bewertung inklusive Radar-Kriterien."""
    user_id = get_user_id(user_name)
    data = {
        "user_id": user_id,
        "drink_aName": drink_name,
        "rating": rating, 
        "remark": remark,
        "design": design,
        "taste": taste,
        "vibe": vibe,
        "image_url": image_url
    }
    supabase.table("Ratings").insert(data).execute()

def load_data():
    """Lädt alle Bewertungen inklusive Profil-Namen."""
    result = supabase.table("Ratings").select("*, Profiles(name)").execute()
    return result.data

def delete_last_entry(user_name):
    """Löscht den aktuellsten Eintrag eines bestimmten Users."""
    user_id = get_user_id(user_name)
    result = supabase.table("Ratings")\
        .select("id")\
        .eq("user_id", user_id)\
        .order("id", desc=True)\
        .limit(1)\
        .execute()
    
    if result.data:
        entry_id = result.data[0]["id"]
        supabase.table("Ratings").delete().eq("id", entry_id).execute()
        return True
    return False