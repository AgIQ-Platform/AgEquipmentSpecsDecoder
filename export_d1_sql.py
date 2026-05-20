import sqlite3
import re

SQLITE_DB_PATH = "ag_decoder.db"
MIGRATION_SQL_PATH = "d1_migration.sql"

def main():
    print("Opening SQLite database...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    
    print("Generating D1 compatible SQL dump using iterdump()...")
    with open(MIGRATION_SQL_PATH, "w") as f:
        # D1 SQL executes statement by statement. Let's write it cleanly.
        for line in conn.iterdump():
            # Clean up the line
            line_strip = line.strip()
            
            # Skip PRAGMA statements
            if line_strip.startswith("PRAGMA"):
                continue
            # Skip transaction markers (D1 wraps requests in its own transactions if needed)
            if line_strip in ["BEGIN TRANSACTION;", "COMMIT;"]:
                continue
                
            # Write statement to the file
            f.write(line + "\n")
            
    print(f"SQL dump successfully written to {MIGRATION_SQL_PATH}!")
    conn.close()

if __name__ == "__main__":
    main()
