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

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("--- Check Steiger 580 ranges ---")
    cur.execute("""
        SELECT make_model_key, year, serial_start, serial_raw
        FROM serial_number_ranges
        WHERE make_model_key LIKE '%steiger580%'
        ORDER BY year;
    """)
    for r in cur.fetchall():
        print(f"Key: {r[0]:<35} | Year: {r[1]:<5} | Start: {r[2]} | Raw: {r[3]}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
