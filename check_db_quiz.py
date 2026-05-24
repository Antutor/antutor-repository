from back.database import supabase

print("Questions:")
res = supabase.table("questions").select("*").limit(1).execute()
print(res.data)

print("Quiz Attempts:")
res = supabase.table("quiz_attempts").select("*").limit(1).execute()
print(res.data)

print("Quiz Answers:")
res = supabase.table("quiz_answers").select("*").limit(1).execute()
print(res.data)

print("Sessions:")
res = supabase.table("sessions").select("session_id, hakes_gain").limit(1).execute()
print(res.data)
