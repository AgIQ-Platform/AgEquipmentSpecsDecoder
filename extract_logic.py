import psycopg2

user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"
db = "agiq_data_db_prod"

conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
cur = conn.cursor()

# Get some top makes (matching exact keys in makes table if possible)
print("\n--- DETAILED LOOK AT TOP MAKES ---")

# Let's write a safe print helper
def safe_str(val):
    return str(val) if val is not None else "None"

makes_to_inspect = ['john-deere', 'case-ih', 'caterpillar', 'new-holland', 'bobcat', 'kubota', 'massey-ferguson']

for m in makes_to_inspect:
    print(f"\n=========================================")
    print(f"MAKE: {m}")
    print(f"=========================================")
    cur.execute("""
        SELECT make_model_key, year, serial_start, serial_raw, confidence, source 
        FROM serial_number_ranges 
        WHERE make_model_key LIKE %s
        ORDER BY year DESC, serial_start
        LIMIT 8;
    """, (m + '%',))
    
    rows = cur.fetchall()
    if not rows:
        print("  No records found matching this prefix.")
    for r in rows:
        print(f"  ModelKey: {safe_str(r[0]):<35} | Year: {safe_str(r[1]):<6} | Start: {safe_str(r[2]):<20} | Raw: {safe_str(r[3]):<20} | Src: {safe_str(r[5])}")

cur.close()
conn.close()
