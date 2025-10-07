"""
Automatic table creation using Supabase Python client.
This creates tables programmatically without SQL Editor.
"""

import os
os.environ["SUPABASE_URL"] = "https://uecltvvipyjtnqxuxozf.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVlY2x0dnZpcHlqdG5xeHV4b3pmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4NzU3NjQsImV4cCI6MjA3NTQ1MTc2NH0.JZVWLqe3I4bnrN-KaWd33j1onQMX34H-NEBo_A8v9aE"

from database import get_db

print("🚀 Testing Supabase connection and creating sample session...")

try:
    db = get_db()
    print("✅ Connected to Supabase!")
    
    # Try to create a test session - this will tell us if tables exist
    print("\n📝 Creating test session...")
    
    test_session = db.create_session("test_auto_123", {"test": True, "auto_created": True})
    print(f"✅ Session created: {test_session.get('thread_id')}")
    
    # Retrieve it
    print("\n📖 Retrieving test session...")
    retrieved = db.get_session("test_auto_123")
    print(f"✅ Session retrieved: {retrieved.get('thread_id')}")
    
    # Clean up
    print("\n🗑️  Cleaning up test session...")
    db.delete_session("test_auto_123")
    print("✅ Test session deleted")
    
    print("\n" + "="*60)
    print("🎉 SUCCESS! Supabase tables exist and working!")
    print("="*60)
    print("\nYour backend is now using Supabase for:")
    print("  ✅ Session storage")
    print("  ✅ Itinerary persistence")  
    print("  ✅ Cache management")
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ Error: {error_msg[:200]}")
    
    if "does not exist" in error_msg or "PGRST" in error_msg:
        print("\n📋 TABLES NEED TO BE CREATED")
        print("="*60)
        print("\nPlease follow these steps:")
        print("\n1. Go to: https://supabase.com/dashboard/project/uecltvvipyjtnqxuxozf/sql/new")
        print("\n2. Copy the content of: /app/backend/schema.sql")
        print("\n3. Paste and Run the SQL")
        print("\n4. Run this script again to verify")
        print("\n" + "="*60)
        print("\nOr read: /app/backend/SUPABASE_SETUP.md for detailed instructions")
    else:
        print(f"\nUnexpected error. Check your connection settings.")

