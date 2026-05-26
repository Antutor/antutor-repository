import os
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from supabase import create_client, Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    res = supabase.table("chat_logs").select("news_urls").limit(1).execute()
    print("Column 'news_urls' exists!")
except Exception as e:
    print("Error:", e)
