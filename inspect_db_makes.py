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
    
    # Check top makes in serial_number_ranges
    print("--- Top makes in serial_number_ranges (local) ---")
    cur.execute("""
        SELECT SPLIT_PART(make_model_key, '-', 1) as make, COUNT(*), MIN(year), MAX(year)
        FROM serial_number_ranges
        GROUP BY make
        ORDER BY COUNT(*) DESC
        LIMIT 20;
    """)
    for r in cur.fetchall():
        print(f"Make: {r[0]:<20} | Count: {r[1]:<6} | Years: {r[2]} - {r[3]}")

    # Check for fendt, challenger, claas, kubota ranges specifically
    print("\n--- Check specific WMC codes ---")
    for wmc in ["WAM", "AG3", "AGC", "WAC", "ZJA", "ZDA", "JEE"]:
        cur.execute("SELECT company, country_code, make_key FROM wmc_codes WHERE wmc_code = %s;", (wmc,))
        r = cur.fetchone()
        if r:
            print(f"WMC: {wmc} | Company: {r[0]:<30} | Country: {r[1]:<5} | Make Key: {r[2]}")
        else:
            print(f"WMC: {wmc} not found!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
