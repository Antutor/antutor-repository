import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'back'))

from database import supabase

res = supabase.table("semantic_cache").select("*").execute()
print("semantic_cache rows count:", len(res.data))
for row in res.data:
    print(f"ID: {row.get('id')}, Concept: {row.get('concept')}, User Answer: '{row.get('user_answer')[:60]}'")
