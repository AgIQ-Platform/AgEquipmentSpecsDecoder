import os
import psycopg2

def load_env():
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v

load_env()
DATABASE_URL = os.environ.get("DATABASE_URL")

def list_tables():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print("Tables in public schema:")
    for t in tables:
        print(f"  - {t[0]}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_tables()
