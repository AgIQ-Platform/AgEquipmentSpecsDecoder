import psycopg2

# Connection details
user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"
db = "agiq_data_db_prod"

conn = psycopg2.connect(
    dbname=db,
    user=user,
    password=password,
    host=host,
    port=port
)
cur = conn.cursor()

# Get top 20 makes by range counts
print("\n--- TOP 20 MAKES IN SERIAL NUMBER RANGES ---")
cur.execute("""
    SELECT SPLIT_PART(make_model_key, '-', 1) as make, COUNT(*), MIN(year), MAX(year)
    FROM serial_number_ranges
    GROUP BY make
    ORDER BY COUNT(*) DESC
    LIMIT 20;
""")
for r in cur.fetchall():
    print(f"  Make: {r[0]:<15} | Ranges Count: {r[1]:<6} | Years: {r[2]} - {r[3]}")

# Get sample of John Deere (john-deere) ranges
print("\n--- SAMPLE JOHN DEERE RANGES ---")
cur.execute("""
    SELECT make_model_key, year, serial_start, serial_raw, confidence, source 
    FROM serial_number_ranges 
    WHERE make_model_key LIKE 'john-deere%' 
    LIMIT 10;
""")
for r in cur.fetchall():
    print(f"  Key: {r[0]:<30} | Year: {r[1]} | Start: {r[2]:<20} | Raw: {r[3]:<20} | Source: {r[5]}")

# Get sample of Case IH (case-ih) ranges
print("\n--- SAMPLE CASE IH RANGES ---")
cur.execute("""
    SELECT make_model_key, year, serial_start, serial_raw, confidence, source 
    FROM serial_number_ranges 
    WHERE make_model_key LIKE 'case-ih%' 
    LIMIT 10;
""")
for r in cur.fetchall():
    print(f"  Key: {r[0]:<30} | Year: {r[1]} | Start: {r[2]:<20} | Raw: {r[3]:<20} | Source: {r[5]}")

cur.close()
conn.close()
