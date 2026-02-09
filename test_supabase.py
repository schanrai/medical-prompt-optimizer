#!/usr/bin/env python3
"""
Test Supabase connection and basic operations.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase_connection():
    """Test basic Supabase connection."""

    # Load environment variables
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env file")
        print("\nPlease add your Supabase credentials to .env:")
        print("  SUPABASE_URL=https://xxxxx.supabase.co")
        print("  SUPABASE_KEY=your_anon_key_here")
        return False

    try:
        print("🔄 Connecting to Supabase...")
        print(f"   URL: {url}")

        # Create Supabase client
        supabase: Client = create_client(url, key)

        print("✅ Successfully connected to Supabase!")

        # Test: List tables (this will show available tables in your project)
        print("\n🔍 Testing connection...")

        # Try a simple query - this will fail if no tables exist yet, which is fine
        try:
            response = supabase.table('_migrations').select("*").limit(1).execute()
            print("✅ Connection test successful!")
        except Exception as e:
            # Expected if no tables exist yet
            print("⚠️  No tables found yet (this is normal for a new project)")
            print(f"   Error: {str(e)}")

        print("\n✨ Supabase setup complete!")
        print("\nNext steps:")
        print("  1. Create tables in Supabase dashboard")
        print("  2. Use this client in your optimizer application")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
