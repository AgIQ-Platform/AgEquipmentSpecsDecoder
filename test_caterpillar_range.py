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

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("--- John Deere WMC Codes in DB ---")
cur.execute("""
    SELECT wmc_code, company, country_code, make_key 
    FROM wmc_codes 
    WHERE make_key LIKE '%deere%' OR company LIKE '%Deere%' OR company LIKE '%DEERE%'
    ORDER BY wmc_code;
""")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()
