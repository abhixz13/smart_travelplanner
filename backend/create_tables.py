import os
import sys

# Set environment variables
os.environ["SUPABASE_URL"] = "https://uecltvvipyjtnqxuxozf.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlY2x0dnZpcHlqdG5xeHV4b3pmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4NzU3NjQsImV4cCI6MjA3NTQ1MTc2NH0.JZVWLqe3I4bnrN-KaWd33j1onQMX34H-NEBo_A8v9aE"

from supabase import create_client

supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_KEY"]

print(f"Connecting to: {supabase_url}")

client = create_client(supabase_url, supabase_key)

# Test connection by trying to query
try:
    response = client.table("user_sessions").select("count", count="exact").limit(1).execute()
    print("✅ Tables exist!")
    print(f"Session count: {response.count}")
except Exception as e:
    print(f"Table check: {str(e)[:200]}")
    if "does not exist" in str(e):
        print("\n⚠️ Tables need to be created")
        print("\n📋 Please run this SQL in Supabase SQL Editor:")
        print("https://supabase.com/dashboard/project/uecltvvipyjtnqxuxozf/sql/new")
        print("\nExecute the content of: /app/backend/schema.sql")
    
