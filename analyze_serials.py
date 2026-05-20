import psycopg2
from collections import Counter

user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"
db = "agiq_data_db_prod"

conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
cur = conn.cursor()

print("\n--- GENERAL SERIAL NUMBER STATS IN AUCTION RESULTS ---")
# Count rows with serial numbers
cur.execute("SELECT COUNT(*) FROM auction_results WHERE serial_number IS NOT NULL AND serial_number != '';")
has_serial = cur.fetchone()[0]
print(f"Total rows with serial numbers: {has_serial}")

# Get top 15 makes in auction results with serial numbers
print("\n--- TOP 15 MAKES WITH SERIAL NUMBERS ---")
cur.execute("""
    SELECT make_key, COUNT(*) 
    FROM auction_results 
    WHERE serial_number IS NOT NULL AND serial_number != ''
    GROUP BY make_key 
    ORDER BY COUNT(*) DESC 
    LIMIT 15;
""")
for r in cur.fetchall():
    print(f"  Make: {str(r[0]):<20} | Count: {r[1]}")

# Get length distribution of serial numbers
print("\n--- SERIAL NUMBER LENGTHS ---")
cur.execute("""
    SELECT LENGTH(serial_number) as len, COUNT(*) 
    FROM auction_results 
    WHERE serial_number IS NOT NULL AND serial_number != ''
    GROUP BY len 
    ORDER BY COUNT(*) DESC 
    LIMIT 10;
""")
for r in cur.fetchall():
    print(f"  Length: {r[0]:<4} | Count: {r[1]}")

# Show some samples from major makes
makes = ['john-deere', 'case-ih', 'caterpillar', 'new-holland', 'bobcat']
for m in makes:
    print(f"\n--- SAMPLES FOR {m.upper()} ---")
    cur.execute("""
        SELECT make_model_key, year, serial_number 
        FROM auction_results 
        WHERE make_key = %s AND serial_number IS NOT NULL AND serial_number != ''
        LIMIT 15;
    """, (m,))
    for r in cur.fetchall():
        print(f"  ModelKey: {str(r[0]):<35} | Year: {str(r[1]):<6} | Serial: {str(r[2])}")

cur.close()
conn.close()
