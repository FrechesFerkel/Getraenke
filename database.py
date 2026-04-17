import os
from supabase import create_client, Client
import pandas as pd

# Verbindung zu Supabase (Bleibt gleich)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_user_id(name):
    """Sucht User oder legt ihn neu an."""
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
    except Exception: return []
    return []

def upload_image(file):
    """Lädt ein Bild hoch."""
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"pic_{timestamp}_{file.name}"
    supabase.storage.from_("tasting-pics").upload(path=file_name, file=file.getvalue(), file_options={"content-type": file.type})
    res = supabase.storage.from_("tasting-pics").get_public_url(file_name)
    return res.public_url if hasattr(res, 'public_url') else str(res)

def save_entry(user_name, drink_name, rating, remark, design, taste, image_url=None):
    """Speichert eine neue Bewertung oder UPDATED eine bestehende."""
    user_id = get_user_id(user_name)
    drink_name_clean = drink_name.strip()
    
    # 1. Prüfen, ob für diesen User und dieses Getränk bereits ein Eintrag existiert
    existing = supabase.table("Ratings")\
        .select("id")\
        .eq("user_id", user_id)\
        .ilike("drink_aName", drink_name_clean)\
        .execute()
    
    data = {
        "user_id": user_id,
        "drink_aName": drink_name_clean,
        "rating": rating, 
        "remark": remark,
        "design": design,
        "taste": taste,
        "image_url": image_url
    }
    
    if existing.data:
        # Falls vorhanden: UPDATE (wir nehmen die ID des alten Eintrags)
        entry_id = existing.data[0]["id"]
        # Wenn kein neues Bild hochgeladen wurde, behalten wir das alte Bild-URL bei
        if not image_url:
            del data["image_url"] 
        
        supabase.table("Ratings").update(data).eq("id", entry_id).execute()
        return "updated"
    else:
        # Falls neu: INSERT
        supabase.table("Ratings").insert(data).execute()
        return "inserted"

def load_data():
    """Lädt alle Bewertungen."""
    result = supabase.table("Ratings").select("*, Profiles(name)").execute()
    return result.data

def delete_last_entry(user_name):
    """Löscht den aktuellsten Eintrag eines Users."""
    user_id = get_user_id(user_name)
    result = supabase.table("Ratings").select("id").eq("user_id", user_id).order("id", desc=True).limit(1).execute()
    if result.data:
        supabase.table("Ratings").delete().eq("id", result.data[0]["id"]).execute()
        return True
    return False

# Die Hilfsfunktion 'has_user_rated_drink' brauchen wir eigentlich nicht mehr, 
# da save_entry das jetzt intern regelt. Wir lassen sie für die app.py aber drin, 
# damit kein Import-Fehler kommt, oder wir löschen sie und passen app.py an.
def has_user_rated_drink(user_name, drink_name):
    user_id = get_user_id(user_name)
    res = supabase.table("Ratings").select("id").eq("user_id", user_id).ilike("drink_aName", drink_name.strip()).execute()
    return len(res.data) > 0