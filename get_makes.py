import psycopg2

user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"
db = "agiq_data_db_prod"

conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'makes' 
    ORDER BY ordinal_position;
""")
cols = cur.fetchall()
print("Columns in makes:")
for col in cols:
    print(f"  - {col[0]} ({col[1]})")

cur.execute("SELECT * FROM makes LIMIT 10;")
rows = cur.fetchall()
col_names = [col[0] for col in cols]
for i, row in enumerate(rows):
    print(f"\nMake {i+1}:")
    for col_name, val in zip(col_names, row):
        print(f"  {col_name}: {val}")

cur.close()
conn.close()
