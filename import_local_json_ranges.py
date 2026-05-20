import os
import sys
import glob
import json
import psycopg2
from psycopg2 import extras

LOCAL_DB_URL = "postgresql://postgres@localhost:5432/dallas_work"
RANGE_TABLES_DIR = "/Users/dallas_work/Downloads/range_tables"

if not os.path.exists(RANGE_TABLES_DIR):
    print(f"Error: Range tables directory not found at {RANGE_TABLES_DIR}")
    sys.exit(1)

print("Starting Local JSON Serial Ranges Bulk Import...")
print(f"Source Directory: {RANGE_TABLES_DIR}")
print(f"Target Database:  {LOCAL_DB_URL}")

try:
    # 1. Connect to local database
    print("\nConnecting to local database...")
    conn = psycopg2.connect(LOCAL_DB_URL)
    cur = conn.cursor()
    
    # 2. Pre-fetch existing ranges for high-performance deduplication
    print("Pre-fetching existing ranges for O(1) in-memory deduplication...")
    cur.execute("SELECT make_model_key, year, serial_start FROM serial_number_ranges;")
    existing_set = set()
    for row in cur.fetchall():
        # Store as normalized lowercase string tuple
        make_model_key = row[0].strip().lower()
        year = int(row[1])
        serial_start = row[2].strip().upper()
        existing_set.add((make_model_key, year, serial_start))
        
    print(f"Loaded {len(existing_set)} existing range combinations.")
    
    # 3. Scan JSON files and build insert batch
    print("\nScanning JSON files and parsing ranges...")
    json_files = glob.glob(os.path.join(RANGE_TABLES_DIR, "*.json"))
    print(f"Found {len(json_files)} JSON files to process.")
    
    insert_rows = []
    duplicate_count = 0
    total_parsed = 0
    
    for i, file_path in enumerate(json_files):
        if i > 0 and i % 200 == 0:
            print(f"  Processed {i} / {len(json_files)} files...")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if not isinstance(data, list):
                    continue
                    
                for record in data:
                    total_parsed += 1
                    
                    # Extract fields
                    make_model_key = record.get("make_model_key", "").strip()
                    year_val = record.get("year")
                    serial_start = record.get("serial_start", "").strip()
                    
                    if not make_model_key or year_val is None or not serial_start:
                        continue
                        
                    year = int(year_val)
                    serial_start_normalized = serial_start.upper()
                    key_tuple = (make_model_key.lower(), year, serial_start_normalized)
                    
                    # Deduplication check
                    if key_tuple in existing_set:
                        duplicate_count += 1
                        continue
                        
                    # Add to set to prevent duplicate records within the JSONs themselves
                    existing_set.add(key_tuple)
                    
                    serial_raw = record.get("serial_raw", serial_start)
                    serial_location = record.get("serial_location", None)
                    source = record.get("source", "JSON Import")
                    confidence = "high"
                    
                    insert_rows.append((
                        make_model_key,
                        year,
                        serial_start,
                        serial_raw,
                        serial_location,
                        confidence,
                        source
                    ))
        except Exception as e:
            print(f"Error parsing file {os.path.basename(file_path)}: {e}")
            
    print(f"\nParsing completed:")
    print(f"  Total records parsed from JSON files: {total_parsed}")
    print(f"  Existing/duplicate records skipped:  {duplicate_count}")
    print(f"  New unique records to insert:        {len(insert_rows)}")
    
    # 4. Bulk insert new ranges
    if insert_rows:
        print(f"\nBulk inserting {len(insert_rows)} new ranges in optimized batches...")
        batch_size = 10000
        total_inserted = 0
        
        for idx in range(0, len(insert_rows), batch_size):
            chunk = insert_rows[idx:idx + batch_size]
            extras.execute_values(
                cur,
                """
                INSERT INTO serial_number_ranges (make_model_key, year, serial_start, serial_raw, serial_location, confidence, source)
                VALUES %s;
                """,
                chunk
            )
            conn.commit()
            total_inserted += len(chunk)
            print(f"  Inserted {total_inserted} / {len(insert_rows)} records...")
            
        print(f"Successfully inserted {total_inserted} records locally!")
    else:
        print("\nNo new range records to insert. Local database is already up-to-date!")
        
    # Get final count
    cur.execute("SELECT COUNT(*) FROM serial_number_ranges;")
    final_count = cur.fetchone()[0]
    print(f"\nFinal local serial_number_ranges count: {final_count} ranges.")
    
    cur.close()
    conn.close()
    print("Local JSON serial ranges import complete!")
    
except Exception as e:
    print(f"Error during import: {e}")
    sys.exit(1)
