import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(url, key)
response = supabase.table('questions').select('*').limit(5).execute()
for q in response.data:
    print(f"Q: {q.get('question_text')}")
    print(f" 1: {q.get('option_1')}")
    print(f" 2: {q.get('option_2')}")
    print(f" 3: {q.get('option_3')}")
    print(f" 4: {q.get('option_4')}")
    print(f" 5: {q.get('option_5')}")
