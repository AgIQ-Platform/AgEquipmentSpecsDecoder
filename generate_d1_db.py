import os
import sqlite3
import psycopg2

RENDER_DATABASE_URL = "postgresql://agiq_data_db_prod_user:65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY@dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com/agiq_data_db_prod"
SQLITE_DB_PATH = "ag_decoder.db"

def main():
    print("Connecting to remote Render Postgres...", flush=True)
    pg_conn = psycopg2.connect(RENDER_DATABASE_URL)
    pg_cur = pg_conn.cursor()

    if os.path.exists(SQLITE_DB_PATH):
        print(f"Removing existing local SQLite file {SQLITE_DB_PATH}...", flush=True)
        os.remove(SQLITE_DB_PATH)

    print("Connecting to local SQLite database...", flush=True)
    lite_conn = sqlite3.connect(SQLITE_DB_PATH)
    lite_cur = lite_conn.cursor()

    # Create tables
    print("Creating SQLite tables...", flush=True)
    lite_cur.execute("""
        CREATE TABLE wmc_codes (
            wmc_code TEXT PRIMARY KEY,
            company TEXT,
            country_code TEXT,
            make_key TEXT
        );
    """)

    lite_cur.execute("""
        CREATE TABLE serial_number_ranges (
            make_model_key TEXT,
            year INTEGER,
            serial_start TEXT,
            confidence TEXT
        );
    """)
    # Add indexes for fast performance on serial_number_ranges
    lite_cur.execute("CREATE INDEX idx_ranges_make_model_key ON serial_number_ranges (make_model_key);")
    lite_cur.execute("CREATE INDEX idx_ranges_serial_start ON serial_number_ranges (serial_start);")

    lite_cur.execute("""
        CREATE TABLE auction_results (
            make_model_key TEXT,
            year INTEGER,
            serial_number TEXT,
            price INTEGER,
            sold_date TEXT,
            state_code TEXT,
            raw_auctioneer TEXT
        );
    """)
    lite_cur.execute("CREATE INDEX idx_auction_make_model_key ON auction_results (make_model_key);")

    # 1. Fetching wmc_codes
    print("Fetching and migrating 'wmc_codes'...", flush=True)
    pg_cur.execute("SELECT wmc_code, company, country_code, make_key FROM wmc_codes;")
    rows = pg_cur.fetchall()
    lite_cur.executemany("""
        INSERT OR REPLACE INTO wmc_codes (wmc_code, company, country_code, make_key)
        VALUES (?, ?, ?, ?);
    """, [(r[0].strip() if r[0] else None, 
           r[1].strip() if r[1] else None, 
           r[2].strip() if r[2] else None, 
           r[3].strip() if r[3] else None) for r in rows])
    lite_conn.commit()
    print(f"Migrated {len(rows):,} wmc_codes.", flush=True)

    # 2. Fetching serial_number_ranges
    print("Fetching and migrating 'serial_number_ranges'...", flush=True)
    pg_cur.execute("SELECT make_model_key, year, serial_start, confidence FROM serial_number_ranges;")
    
    # We will fetch and insert in chunks to keep memory usage low
    chunk_size = 50000
    inserted_count = 0
    while True:
        rows = pg_cur.fetchmany(chunk_size)
        if not rows:
            break
        
        batch = []
        for r in rows:
            batch.append((
                r[0].strip() if r[0] else None,
                r[1],
                r[2].strip() if r[2] else None,
                r[3].strip() if r[3] else None
            ))
        
        lite_cur.executemany("""
            INSERT INTO serial_number_ranges (make_model_key, year, serial_start, confidence)
            VALUES (?, ?, ?, ?);
        """, batch)
        lite_conn.commit()
        inserted_count += len(batch)
        print(f"Migrated {inserted_count:,} serial_number_ranges...", flush=True)

    # 3. Fetching auction_results (where price IS NOT NULL AND price > 0) using server-side cursor
    print("Fetching count of valid 'auction_results'...", flush=True)
    pg_cur.execute("SELECT COUNT(*) FROM auction_results WHERE price IS NOT NULL AND price > 0;")
    valid_count = pg_cur.fetchone()[0]
    print(f"Found {valid_count:,} valid auction results with price > 0.", flush=True)

    print("Fetching and migrating 'auction_results' using server-side cursor...", flush=True)
    
    # We must use a named server-side cursor to avoid client buffering of 1.7M rows
    pg_cur_server = pg_conn.cursor(name='auction_results_migration_cursor')
    pg_cur_server.itersize = chunk_size
    pg_cur_server.execute("""
        SELECT make_model_key, year, serial_number, price, sold_date, state_code, raw_auctioneer 
        FROM auction_results 
        WHERE price IS NOT NULL AND price > 0;
    """)

    inserted_sales = 0
    while True:
        rows = pg_cur_server.fetchmany(chunk_size)
        if not rows:
            break
        
        batch = []
        for r in rows:
            batch.append((
                r[0].strip() if r[0] else None,
                r[1],
                r[2].strip() if r[2] else None,
                r[3],
                str(r[4]) if r[4] else None,
                r[5].strip() if r[5] else None,
                r[6].strip() if r[6] else None
            ))
        
        lite_cur.executemany("""
            INSERT INTO auction_results (make_model_key, year, serial_number, price, sold_date, state_code, raw_auctioneer)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, batch)
        lite_conn.commit()
        inserted_sales += len(batch)
        print(f"Migrated {inserted_sales:,} / {valid_count:,} auction_results...", flush=True)

    pg_cur_server.close()

    print("Optimizing SQLite database (VACUUM and ANALYZE)...", flush=True)
    lite_cur.execute("VACUUM;")
    lite_conn.commit()
    print("SQLite database successfully created and optimized!", flush=True)
    
    # Print file size
    db_size = os.path.getsize(SQLITE_DB_PATH) / (1024 * 1024)
    print(f"SQLite DB File Size: {db_size:.2f} MB", flush=True)

    pg_cur.close()
    pg_conn.close()
    lite_cur.close()
    lite_conn.close()

if __name__ == "__main__":
    main()
