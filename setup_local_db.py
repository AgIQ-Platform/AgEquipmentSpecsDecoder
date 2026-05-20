import os
import sys
import psycopg2
from psycopg2 import extras

def load_env():
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v

load_env()
RENDER_DB_URL = os.environ.get("DATABASE_URL")
LOCAL_DB_URL = "postgresql://postgres@localhost:5432/dallas_work"

if not RENDER_DB_URL:
    print("Error: DATABASE_URL not found in .env file.")
    sys.exit(1)

print("Starting Local PostgreSQL Database Setup & Data Migration...")
print(f"Source (Render): {RENDER_DB_URL.split('@')[1] if '@' in RENDER_DB_URL else RENDER_DB_URL}")
print(f"Target (Local):  localhost:5432/dallas_work")

try:
    # 1. Connect to both databases
    print("\nConnecting to databases...")
    conn_remote = psycopg2.connect(RENDER_DB_URL)
    conn_local = psycopg2.connect(LOCAL_DB_URL)
    
    cur_remote = conn_remote.cursor(name="remote_migration_cursor") # Server-side cursor for remote DB
    cur_local = conn_local.cursor()
    
    # 2. Enable uuid-ossp extension locally
    cur_local.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    cur_local.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
    
    # 3. Create tables locally
    print("\nReplicating table schemas locally...")
    
    # Create wmc_codes
    cur_local.execute("DROP TABLE IF EXISTS wmc_codes CASCADE;")
    cur_local.execute("""
        CREATE TABLE wmc_codes (
            wmc_code varchar NOT NULL,
            company varchar NOT NULL,
            company_address varchar NULL,
            company_website varchar NULL,
            make_key varchar NULL,
            country_code varchar NULL,
            source varchar NULL,
            created_at timestamp NOT NULL DEFAULT NOW(),
            PRIMARY KEY (wmc_code)
        );
    """)
    
    # Create serial_number_ranges
    cur_local.execute("DROP TABLE IF EXISTS serial_number_ranges CASCADE;")
    cur_local.execute("""
        CREATE TABLE serial_number_ranges (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            make_model_key varchar NOT NULL,
            year integer NOT NULL,
            serial_start varchar NOT NULL,
            serial_raw varchar NULL,
            serial_location varchar NULL,
            drive_type varchar NULL,
            footnotes jsonb NULL,
            variant_codes jsonb NULL,
            source_page varchar NULL,
            source_pdf integer NULL,
            confidence varchar NULL,
            source varchar NULL,
            created_at timestamp NOT NULL DEFAULT NOW()
        );
    """)
    conn_local.commit()
    print("Schemas successfully replicated!")
    
    # 4. Migrate wmc_codes
    print("\nMigrating wmc_codes (1,431 records)...")
    cur_remote_simple = conn_remote.cursor() # Needs separate cursor since cur_remote is server-side
    cur_remote_simple.execute("""
        SELECT wmc_code, company, company_address, company_website, make_key, country_code, source, created_at 
        FROM wmc_codes;
    """)
    wmc_rows = cur_remote_simple.fetchall()
    
    if wmc_rows:
        extras.execute_values(
            cur_local,
            """
            INSERT INTO wmc_codes (wmc_code, company, company_address, company_website, make_key, country_code, source, created_at)
            VALUES %s ON CONFLICT (wmc_code) DO NOTHING;
            """,
            wmc_rows
        )
        conn_local.commit()
    print(f"Successfully migrated {len(wmc_rows)} WMC codes!")
    cur_remote_simple.close()
    
    # 5. Migrate serial_number_ranges
    print("\nMigrating serial_number_ranges (284,931 records)...")
    cur_remote.itersize = 10000 # Fetch in chunks of 10,000 rows
    cur_remote.execute("""
        SELECT id, make_model_key, year, serial_start, serial_raw, serial_location, drive_type, footnotes, variant_codes, source_page, source_pdf, confidence, source, created_at 
        FROM serial_number_ranges;
    """)
    
    batch = []
    total_migrated = 0
    batch_count = 0
    
    while True:
        rows = cur_remote.fetchmany(10000)
        if not rows:
            break
            
        # Convert footnotes/variant_codes to JSON strings if they aren't already
        clean_rows = []
        for r in rows:
            clean_rows.append((
                r[0], r[1], r[2], r[3], r[4], r[5], r[6],
                extras.Json(r[7]) if r[7] is not None else None,
                extras.Json(r[8]) if r[8] is not None else None,
                r[9], r[10], r[11], r[12], r[13]
            ))
            
        extras.execute_values(
            cur_local,
            """
            INSERT INTO serial_number_ranges (id, make_model_key, year, serial_start, serial_raw, serial_location, drive_type, footnotes, variant_codes, source_page, source_pdf, confidence, source, created_at)
            VALUES %s ON CONFLICT (id) DO NOTHING;
            """,
            clean_rows
        )
        conn_local.commit()
        
        total_migrated += len(rows)
        batch_count += 1
        print(f"  Batch {batch_count}: Migrated {total_migrated} ranges...")
        
    print(f"\nMigration complete! Total ranges migrated: {total_migrated}")
    
    # Close resources
    cur_remote.close()
    cur_local.close()
    conn_remote.close()
    conn_local.close()
    print("Database migration finished successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    sys.exit(1)
