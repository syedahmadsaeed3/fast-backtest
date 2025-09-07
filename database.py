from settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client


url: str = SUPABASE_URL
key: str = SUPABASE_KEY
supabase: Client = create_client(url, key)


def get_supabase():
    return supabase