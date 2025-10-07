"""
Database initialization script.
Creates tables in Supabase if they don't exist.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database tables."""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        return False
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    
    try:
        client = create_client(supabase_url, supabase_key)
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        if not os.path.exists(schema_path):
            print("❌ Error: schema.sql not found")
            return False
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        print("\n📋 Database Schema:")
        print("=" * 60)
        print("Please execute the following SQL in your Supabase SQL Editor:")
        print("(Go to: Supabase Dashboard → SQL Editor → New Query)")
        print("=" * 60)
        print(schema_sql)
        print("=" * 60)
        
        # Test connection by querying a table
        print("\n🧪 Testing database connection...")
        
        try:
            # Try to query user_sessions table
            response = client.table("user_sessions").select("count", count="exact").limit(1).execute()
            print("✅ Database connection successful!")
            print(f"✅ user_sessions table exists")
            return True
            
        except Exception as e:
            error_str = str(e)
            if "relation" in error_str and "does not exist" in error_str:
                print("\n⚠️  Tables not yet created.")
                print("\n📝 Action Required:")
                print("1. Copy the SQL schema above")
                print("2. Go to Supabase Dashboard → SQL Editor")
                print("3. Create a new query and paste the schema")
                print("4. Run the query to create tables")
                print("5. Run this script again to verify")
                return False
            else:
                print(f"❌ Error querying database: {error_str}")
                return False
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False


def test_database_operations():
    """Test basic database operations."""
    from database import get_db
    
    print("\n🧪 Testing database operations...")
    
    try:
        db = get_db()
        
        # Test session creation
        print("  → Creating test session...")
        test_thread_id = "test_init_session"
        
        session = db.create_session(test_thread_id, {"test": True})
        print(f"  ✅ Session created: {session.get('thread_id')}")
        
        # Test session retrieval
        print("  → Retrieving test session...")
        retrieved = db.get_session(test_thread_id)
        print(f"  ✅ Session retrieved: {retrieved.get('thread_id')}")
        
        # Test session deletion
        print("  → Deleting test session...")
        db.delete_session(test_thread_id)
        print("  ✅ Session deleted")
        
        print("\n✅ All database operations working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database operations test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 AI Travel Planner - Database Initialization")
    print("=" * 60)
    
    # Initialize database
    if init_database():
        print("\n" + "=" * 60)
        
        # Ask user if they want to test operations
        response = input("\n🧪 Tables exist! Test database operations? (y/n): ")
        if response.lower() == 'y':
            test_database_operations()
    
    print("\n" + "=" * 60)
    print("✨ Database initialization complete!")
    print("=" * 60)
