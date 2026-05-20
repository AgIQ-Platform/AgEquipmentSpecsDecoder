import os
import psycopg2
import re

def load_env():
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v

load_env()
DATABASE_URL = os.environ.get("DATABASE_URL")

def extract_seq_num(val):
    val = val.strip()
    if val.isdigit():
        return int(val)
    if len(val) == 17:
        seq_str = val[11:17]
        if seq_str.isdigit():
            return int(seq_str)
    return None

def test_logic(serial):
    serial_clean = serial.strip().upper()
    print(f"Testing serial: {serial_clean}")
    
    # Slices
    wmc = serial_clean[0:3]
    model_part = serial_clean[3:8]
    check_digit = serial_clean[8]
    year_code = serial_clean[9]
    plant_code = serial_clean[10]
    seq_part = serial_clean[11:17]
    
    model_clean = model_part.lstrip('0')
    translated_model = model_clean
    translated_model_key = None
    
    # Modern Waterloo: 9[HP][Config] (excluding R and T as configuration letters)
    m_modern = re.match(r"^9(\d{3})([A-Z])$", model_clean)
    # Legacy Waterloo: 9[HP][R/T]
    m_legacy = re.match(r"^9(\d{3})([RT])$", model_clean)
    
    if seq_part.isdigit():
        seq_num = int(seq_part)
        if m_modern and m_modern.group(2) not in ['R', 'T']:
            hp = m_modern.group(1)
            suffix = m_modern.group(2)
            series = "9R"
            if seq_num < 100000:
                series = "9R"
            elif 900000 <= seq_num < 1000000:
                series = "9RT"
            elif (500000 <= seq_num < 600000) or (700000 <= seq_num < 900000):
                series = "9RX"
            
            translated_model = f"{series} {hp}"
            translated_model_key = f"john-deere-{series.lower()}{hp}"
        elif m_legacy:
            hp = m_legacy.group(1)
            suffix = m_legacy.group(2)
            config = suffix
            if seq_num < 100000:
                config = "R"
            elif 900000 <= seq_num < 1000000:
                config = "RT"
            elif (500000 <= seq_num < 600000) or (700000 <= seq_num < 900000):
                config = "RX"
            
            translated_model = f"9{hp}{config}"
            translated_model_key = f"john-deere-9{hp}{config.lower()}"

    print(f"  Parsed Model Clean: {model_clean}")
    print(f"  Translated Model: {translated_model}")
    print(f"  Translated Model Key: {translated_model_key}")
    
    # Query database sequence range
    is_seq_determined = False
    year_val = None
    if translated_model_key and seq_part.isdigit():
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                SELECT year, serial_start, confidence 
                FROM serial_number_ranges 
                WHERE make_model_key = %s 
                ORDER BY serial_start;
            """, (translated_model_key,))
            ranges = cur.fetchall()
            cur.close()
            conn.close()
            
            best_year = None
            best_start = None
            for yr, start_val, conf in ranges:
                start_seq = extract_seq_num(start_val)
                if start_seq is not None:
                    if seq_num >= start_seq:
                        if best_start is None or start_seq > best_start:
                            best_start = start_seq
                            best_year = yr
            if best_year:
                year_val = best_year
                is_seq_determined = True
        except Exception as e:
            print(f"Error querying sequence year: {e}")
            
    print(f"  Determined Year: {year_val} (Sequence verified: {is_seq_determined})")

if __name__ == "__main__":
    test_logic("1RW9440DASA090295")
    print()
    test_logic("1RW9590DAPJ822510")
