import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

res = supabase.table("sessions").select("*").limit(1).execute()
if res.data:
    print(list(res.data[0].keys()))
else:
    print("No sessions found")
