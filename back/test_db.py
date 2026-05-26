import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import supabase

try:
    res = supabase.table("questions").select("*").limit(1).execute()
    print("Columns:", res.data[0].keys() if res.data else "No data")
except Exception as e:
    print("Error:", e)
