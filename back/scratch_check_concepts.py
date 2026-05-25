
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

try:
    response = supabase.table("concepts").select("*").execute()
    print(f"Count: {len(response.data)}")
    for row in response.data:
        print(f"- {row.get('name')}")
except Exception as e:
    print(f"Error: {e}")
