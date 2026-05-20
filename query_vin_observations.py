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

def query_vin():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 1. Count records
    cur.execute("SELECT COUNT(*) FROM vin_observations;")
    count = cur.fetchone()[0]
    print(f"Total rows in vin_observations: {count}")
    
    # 2. Get columns
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'vin_observations'
        ORDER BY ordinal_position;
    """)
    cols = cur.fetchall()
    print("\nColumns in vin_observations:")
    for col in cols:
        print(f"  - {col[0]} ({col[1]})")
        
    # 3. Sample rows
    cur.execute("SELECT * FROM vin_observations LIMIT 3;")
    rows = cur.fetchall()
    col_names = [col[0] for col in cols]
    print("\nSample Rows:")
    for i, row in enumerate(rows):
        print(f"Row {i+1}:")
        for col_name, val in zip(col_names, row):
            print(f"  {col_name}: {val}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    query_vin()
