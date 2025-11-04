import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url=os.getenv("SUPABASE_URL")
supabase_key=os.getenv("SUPABASE_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
supabase:Client=create_client(supabase_url,supabase_key)

# print()
