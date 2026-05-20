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

def inspect_table_schema(table_name):
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    cols = cur.fetchall()
    print(f"\nSchema of {table_name}:")
    for col in cols:
        print(f"  - {col[0]} ({col[1]})")

inspect_table_schema("auction_results")

# Let's count rows in key tables
tables = ["serial_number_ranges", "wmc_codes", "vin_observations", "auction_results"]
print("\nRow Counts:")
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        count = cur.fetchone()[0]
        print(f"  - {t}: {count}")
    except Exception as e:
        print(f"  - {t}: error ({e})")

cur.close()
conn.close()
