import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def load_data():
    try:
        response = supabase.table("Ratings").select("*, Profiles(name)").execute()
        return response.data
    except Exception as e:
        print(f"Fehler beim Laden: {e}")
        return []

def get_unique_drinks():
    # 
    try:
        response = supabase.table("Ratings").select("drink_aName").execute()
        names = list(set([item['drink_aName'] for item in response.data if item['drink_aName']]))
        return sorted(names)
    except Exception as e:
        print(f"Fehler bei Getränkeliste: {e}")
        return []

def get_or_create_user_id(user_name):
    """Prüft ob User existiert und gibt die ID zurück, sonst neu anlegen."""
    # Suche User mit diesem Namen
    res = supabase.table("Profiles").select("id").eq("name", user_name).execute()
    
    if res.data:
        return res.data[0]["id"]
    else:
        # User neu anlegen
        new_user = supabase.table("Profiles").insert({"name": user_name}).execute()
        return new_user.data[0]["id"]

def save_entry(user_name, drink, rating, comment):
    u_id = get_or_create_user_id(user_name)
    
    data = {
        "user_id": u_id,
        "drink_aName": drink,
        "rating": rating,
        "remark": comment
    }
    supabase.table("Ratings").insert(data).execute()