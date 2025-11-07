import os

import google.generativeai as genai
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
llm = genai.GenerativeModel("gemini-2.5-flash")

# Supabase connection
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")

supabase = create_client(url, key)
