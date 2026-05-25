import os
import sys
# Add 'back' directory to sys.path
back_path = os.path.join(os.getcwd(), 'back')
sys.path.append(back_path)

from database import supabase

try:
    res = supabase.table("concepts").select("name").execute()
    print("Available concepts:", [c['name'] for c in res.data])
except Exception as e:
    print("Error fetching concepts:", e)
