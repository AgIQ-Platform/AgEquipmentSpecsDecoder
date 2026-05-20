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

def inspect_table(table_name, limit=5):
    print(f"\n=========================================")
    print(f"INSPECTING TABLE: {table_name}")
    print(f"=========================================")
    
    # Get columns and types
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    cols = cur.fetchall()
    print("Columns:")
    for col in cols:
        print(f"  - {col[0]} ({col[1]})")
        
    # Get sample data
    try:
        cur.execute(f"SELECT * FROM {table_name} LIMIT %s;", (limit,))
        rows = cur.fetchall()
        col_names = [col[0] for col in cols]
        print(f"\nSample Rows (Limit {limit}):")
        for i, row in enumerate(rows):
            print(f"Row {i+1}:")
            for col_name, val in zip(col_names, row):
                print(f"  {col_name}: {val}")
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")

# Inspect key tables
inspect_table("serial_number_ranges", limit=3)
inspect_table("wmc_codes", limit=3)
inspect_table("vin_observations", limit=3)

cur.close()
conn.close()
