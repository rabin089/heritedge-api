import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Try to connect to PostgreSQL
try:
    # First try to connect to postgres database to create our database
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        user="postgres", 
        password="admin",
        database="postgres"  # default postgres database
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if heritage-db exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'heritage-db'")
    exists = cursor.fetchone()
    
    if not exists:
        print("Creating database 'heritage-db'...")
        cursor.execute("CREATE DATABASE \"heritage-db\"")
        print("Database created successfully!")
    else:
        print("Database 'heritage-db' already exists")
    
    # Test connection to our database
    conn.close()
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        user="postgres",
        password="admin", 
        database="heritage-db"
    )
    print("✅ Successfully connected to heritage-db database!")
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection error: {e}")
    print("Make sure PostgreSQL is running and credentials are correct")