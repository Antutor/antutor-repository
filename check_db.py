import os
import sys

# Add back directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'back'))

from back.database import supabase

# fetch 1 row from sessions
res = supabase.table("sessions").select("*").limit(1).execute()
print("Sessions data:", res.data)
