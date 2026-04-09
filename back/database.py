from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Supabase 클라이언트 초기화
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

