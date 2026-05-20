import psycopg2

RENDER_DATABASE_URL = "postgresql://agiq_data_db_prod_user:65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY@dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com/agiq_data_db_prod"

def main():
    print("Connecting to remote Render database...")
    try:
        conn = psycopg2.connect(RENDER_DATABASE_URL)
        cur = conn.cursor()
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cur.fetchall()
        print("Found tables:")
        for t in tables:
            print(f" - {t[0]}")
            
        # Count rows in each table if they exist
        for t in ['wmc_codes', 'serial_number_ranges', 'auction_results']:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                count = cur.fetchone()[0]
                print(f"Row count in '{t}': {count:,}")
            except Exception as e:
                print(f"Error querying '{t}': {e}")
                conn.rollback()
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    main()
