import psycopg2
import sys

# Connection details
user = "agiq_data_db_prod_user"
password = "65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY"
host = "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com"
port = "5432"

db_names = ["agiq_data_db_prod", "agiq_data_db_prod_user", "postgres"]

conn = None
connected_db = None

for db in db_names:
    try:
        print(f"Trying to connect to database: {db} on host {host}...")
        conn = psycopg2.connect(
            dbname=db,
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=5
        )
        connected_db = db
        print(f"Successfully connected to database: {db}!")
        break
    except Exception as e:
        print(f"Failed to connect to database {db}: {e}")

if not conn:
    print("Could not connect to any of the databases.")
    sys.exit(1)

try:
    cur = conn.cursor()
    # List all tables
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """)
    tables = cur.fetchall()
    print("\n--- TABLES IN DATABASE ---")
    for t in tables:
        print(f"{t[0]}.{t[1]}")
    
    # Close connection
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error querying tables: {e}")
