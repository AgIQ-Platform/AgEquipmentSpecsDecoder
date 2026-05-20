import psycopg2

user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"
db = "agiq_data_db_prod"

conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
cur = conn.cursor()

print("\n--- CASE IH RANGES FOR SPECIFIC MODELS ---")
models = ['case-ih-7120magnum', 'case-ih-maxxum125', 'case-ih-580l', 'case-ih-farmall35a']
for m in models:
    print(f"\nRanges for {m}:")
    cur.execute("""
        SELECT year, serial_start, confidence, source 
        FROM serial_number_ranges 
        WHERE make_model_key = %s
        ORDER BY year;
    """, (m,))
    for r in cur.fetchall():
        print(f"  Year: {r[0]} | Start: {r[1]} | Confidence: {r[2]} | Source: {r[3]}")

print("\n--- NEW HOLLAND RANGES FOR SPECIFIC MODELS ---")
nh_models = ['new-holland-t6020', 'new-holland-l228']
for m in nh_models:
    print(f"\nRanges for {m}:")
    cur.execute("""
        SELECT year, serial_start, confidence, source 
        FROM serial_number_ranges 
        WHERE make_model_key = %s
        ORDER BY year;
    """, (m,))
    for r in cur.fetchall():
        print(f"  Year: {r[0]} | Start: {r[1]} | Confidence: {r[2]} | Source: {r[3]}")

cur.close()
conn.close()
