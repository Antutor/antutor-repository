import os
import asyncio
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zpxofmslksixgcvdskzz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-key")
# Assuming key is available in .env
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("chat_logs").select("news_urls, ai_response, turn_number").order("created_at", desc=True).limit(5).execute()
for r in res.data:
    print(f"Turn {r['turn_number']}: news_urls={r['news_urls']}")
