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
# Connect to the remote Render database for read-only research
RENDER_DATABASE_URL = os.environ.get("RENDER_DATABASE_URL")

def main():
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    print("--- Remote John Deere 9-Series PIN Observations ---")
    cur.execute("""
        SELECT make_model_key, vin, COUNT(*) 
        FROM vin_observations 
        WHERE make_model_key LIKE 'john-deere-9%' AND length(vin) = 17
        GROUP BY make_model_key, vin
        ORDER BY make_model_key, COUNT(*) DESC
        LIMIT 60;
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} observed PINs:")
    for row in rows:
        print(f"  Model: {row[0]:<20} | PIN: {row[1]} | Count: {row[2]}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
