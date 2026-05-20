import psycopg2
import time

RENDER_DATABASE_URL = "postgresql://agiq_data_db_prod_user:65H0JQ4MWSdw2KvG0sf4jpW8okzOZvWY@dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com/agiq_data_db_prod"

def main():
    conn = psycopg2.connect(RENDER_DATABASE_URL)
    cur = conn.cursor()
    
    print("Checking unique make_model_keys in serial_number_ranges...")
    t0 = time.time()
    cur.execute("SELECT COUNT(DISTINCT make_model_key) FROM serial_number_ranges;")
    distinct_keys = cur.fetchone()[0]
    print(f"Distinct make_model_keys in ranges: {distinct_keys} (took {time.time()-t0:.2f}s)")

    print("Checking total count of auction_results with price > 0...")
    t0 = time.time()
    cur.execute("SELECT COUNT(*) FROM auction_results WHERE price IS NOT NULL AND price > 0;")
    price_count = cur.fetchone()[0]
    print(f"Auction results with price > 0: {price_count} (took {time.time()-t0:.2f}s)")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
