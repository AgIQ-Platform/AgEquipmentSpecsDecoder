import psycopg2

RENDER_DATABASE_URL = "postgresql://agiq_data_db_prod_user:65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY@dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com/agiq_data_db_prod"

def main():
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    for table in ['wmc_codes', 'serial_number_ranges', 'auction_results']:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}';
        """)
        cols = cur.fetchall()
        print(f"Table: {table}")
        for col in cols:
            print(f"  - {col[0]} ({col[1]})")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
