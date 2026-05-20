import re
import json
from workers import WorkerEntrypoint, Response
from parser import decode_serial, normalize_cat_serial

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Handle CORS preflight options request
        if request.method == "OPTIONS":
            return Response(
                "",
                status=204,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Max-Age": "86400"
                }
            )

        # Parse request inputs
        serial = None
        url = request.url
        
        # 1. Parse GET query parameters
        if "?" in url:
            params = url.split("?", 1)[1]
            for p in params.split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    if k.strip().lower() == "serial":
                        import urllib.parse
                        serial = urllib.parse.unquote(v.strip())

        # 2. Parse POST json body
        if not serial and request.method == "POST":
            try:
                body = await request.json()
                if isinstance(body, dict):
                    serial = body.get("serial")
            except Exception:
                pass

        if not serial:
            return Response(
                json.dumps({"error": "Serial number is required"}),
                status=400,
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            )

        serial_clean = serial.strip().upper()
        db = self.env.DB

        # --- A. WMC LOOKUP ---
        wmc_info = None
        if len(serial_clean) >= 3:
            wmc_code = serial_clean[0:3]
            try:
                wmc_stmt = db.prepare("SELECT wmc_code, company, country_code, make_key FROM wmc_codes WHERE wmc_code = ? LIMIT 1")
                wmc_res = await wmc_stmt.bind(wmc_code).first()
                if wmc_res:
                    # In python workers, results are accessable as attributes or dicts
                    # We will support both safely
                    r_company = getattr(wmc_res, "company", None) or wmc_res.get("company")
                    r_country = getattr(wmc_res, "country_code", None) or wmc_res.get("country_code")
                    r_make = getattr(wmc_res, "make_key", None) or wmc_res.get("make_key")
                    
                    wmc_info = {
                        "company": r_company.strip() if r_company else "Unknown",
                        "country": r_country.strip() if r_country else "Unknown",
                        "make_key": r_make.strip() if r_make else "unknown"
                    }
            except Exception as e:
                print(f"Error executing WMC lookup in Worker: {e}")

        # --- B. RANGE LOOKUP ---
        best_match = None
        length = len(serial_clean)
        
        # 1. Caterpillar Suffix / PIN Range Lookup
        is_cat = serial_clean.startswith("CAT") or (length in [8, 9] and any(serial_clean.startswith(x) for x in ["8", "9", "D", "E", "L", "A", "J", "K", "R", "W"]))
        if is_cat:
            input_prefix, input_seq = normalize_cat_serial(serial_clean)
            if input_prefix:
                try:
                    cat_stmt = db.prepare("""
                        SELECT make_model_key, year, serial_start, confidence 
                        FROM serial_number_ranges 
                        WHERE make_model_key LIKE ? AND (
                            serial_start LIKE ? OR 
                            serial_start LIKE ?
                        )
                        ORDER BY serial_start, make_model_key;
                    """)
                    cat_res = await cat_stmt.bind("caterpillar%", f"%{input_prefix}%", f"{input_prefix}%").all()
                    
                    best_cat = None
                    for r in cat_res.results:
                        r_key = getattr(r, "make_model_key", None) or r.get("make_model_key")
                        r_year = getattr(r, "year", None) or r.get("year")
                        r_start = getattr(r, "serial_start", None) or r.get("serial_start")
                        r_conf = getattr(r, "confidence", None) or r.get("confidence")
                        
                        r_prefix, r_seq = normalize_cat_serial(r_start)
                        if r_prefix == input_prefix:
                            if input_seq >= r_seq:
                                if best_cat is None or r_seq > best_cat["r_seq"]:
                                    best_cat = {
                                        "make_model_key": r_key,
                                        "year": r_year,
                                        "serial_start": r_start,
                                        "confidence": r_conf,
                                        "r_seq": r_seq
                                    }
                    if best_cat:
                        best_match = {
                            "make_model_key": best_cat["make_model_key"],
                            "year": best_cat["year"],
                            "serial_start": best_cat["serial_start"],
                            "confidence": best_cat["confidence"]
                        }
                except Exception as e:
                    print(f"Error in Caterpillar D1 lookup: {e}")
                    
        # 2. General Prefix Range Lookup if no Caterpillar match
        if not best_match:
            is_jd_pin = (length == 17 and wmc_info and wmc_info["make_key"] == "john-deere")
            prefix = ""
            make_filter = None
            
            if serial_clean.startswith("CAT") and length == 17:
                prefix = serial_clean[0:12]
                make_filter = "caterpillar%"
            elif is_jd_pin:
                prefix = serial_clean[0:8]
                make_filter = "john-deere%"
            elif length == 13 and (serial_clean.startswith("RW") or serial_clean.startswith("T0") or serial_clean.startswith("LU")):
                prefix = serial_clean[0:7]
                make_filter = "john-deere%"
            elif length == 9 and (serial_clean.startswith("Z") or serial_clean.startswith("Y") or serial_clean.startswith("H")):
                prefix = serial_clean[0:3]
            elif length == 13 and (serial_clean[0:2].isdigit() or serial_clean[0:3].isdigit()):
                prefix = serial_clean[0:6]
            else:
                prefix = serial_clean[0:min(6, length)]
                
            try:
                if make_filter:
                    range_stmt = db.prepare("""
                        SELECT make_model_key, year, serial_start, confidence 
                        FROM serial_number_ranges 
                        WHERE make_model_key LIKE ? AND serial_start LIKE ? 
                        ORDER BY serial_start, make_model_key;
                    """)
                    range_res = await range_stmt.bind(make_filter, f"{prefix}%").all()
                else:
                    range_stmt = db.prepare("""
                        SELECT make_model_key, year, serial_start, confidence 
                        FROM serial_number_ranges 
                        WHERE serial_start LIKE ? 
                        ORDER BY serial_start, make_model_key;
                    """)
                    range_res = await range_stmt.bind(f"{prefix}%").all()
                    
                for r in range_res.results:
                    r_key = getattr(r, "make_model_key", None) or r.get("make_model_key")
                    r_year = getattr(r, "year", None) or r.get("year")
                    r_start = getattr(r, "serial_start", None) or r.get("serial_start")
                    r_conf = getattr(r, "confidence", None) or r.get("confidence")
                    
                    if not r_start:
                        continue
                    clean_start = r_start.strip().upper()
                    if serial_clean >= clean_start:
                        best_match = {
                            "make_model_key": r_key,
                            "year": r_year,
                            "serial_start": r_start,
                            "confidence": r_conf
                        }
            except Exception as e:
                print(f"Error in general D1 range lookup: {e}")

        # --- C. JD SEQUENCE RANGE PRE-QUERY (Waterloo 9-Series / Combines) ---
        jd_seq_ranges = []
        if length == 17:
            try:
                model_part = serial_clean[3:8]
                model_clean = model_part.lstrip('0')
                
                m_modern = re.match(r"^9(\d{3})([A-Z])$", model_clean)
                m_x9 = re.match(r"^X9(1[01])([A-Z])$", model_clean)
                
                translated_keys = []
                if m_modern:
                    hp = m_modern.group(1)
                    config = m_modern.group(2)
                    if config in ["R", "RT", "RX"]:
                        translated_keys.append(f"john-deere-9{config.lower()}{hp}")
                    translated_keys.append(f"john-deere-9{hp}{config.lower()}")
                elif m_x9:
                    sub_model = m_x9.group(1)
                    translated_keys.append(f"john-deere-x9{sub_model}00")
                    
                for tk in translated_keys:
                    jd_stmt = db.prepare("SELECT year, serial_start, confidence FROM serial_number_ranges WHERE make_model_key = ? ORDER BY serial_start")
                    jd_res = await jd_stmt.bind(tk).all()
                    for r in jd_res.results:
                        r_yr = getattr(r, "year", None) or r.get("year")
                        r_start = getattr(r, "serial_start", None) or r.get("serial_start")
                        r_conf = getattr(r, "confidence", None) or r.get("confidence")
                        jd_seq_ranges.append((r_yr, r_start, r_conf))
            except Exception as e:
                print(f"Error pre-fetching John Deere sequence ranges: {e}")

        # --- D. FIRST PASS DECODING ---
        decoded = decode_serial(
            serial_clean, 
            db_match=best_match, 
            wmc_info=wmc_info, 
            similar_sales=[], 
            jd_seq_ranges=jd_seq_ranges, 
            pre_resolved=True
        )

        # --- E. FETCH SIMILAR SALES & SECOND PASS ---
        similar_sales = []
        if decoded.get("model") and decoded.get("model") != "Unknown":
            make_key = decoded.get("make_key") or "unknown"
            model_key = f"{make_key}-{decoded['model'].lower().replace(' ', '')}"
            try:
                sales_stmt = db.prepare("""
                    SELECT year, serial_number, price, sold_date, state_code, raw_auctioneer 
                    FROM auction_results 
                    WHERE make_model_key = ? AND price IS NOT NULL AND price > 0
                    ORDER BY sold_date DESC 
                    LIMIT 5;
                """)
                sales_res = await sales_stmt.bind(model_key).all()
                for s in sales_res.results:
                    s_yr = getattr(s, "year", None) or s.get("year")
                    s_ser = getattr(s, "serial_number", None) or s.get("serial_number")
                    s_pr = getattr(s, "price", None) or s.get("price")
                    s_dt = getattr(s, "sold_date", None) or s.get("sold_date")
                    s_st = getattr(s, "state_code", None) or s.get("state_code")
                    s_auc = getattr(s, "raw_auctioneer", None) or s.get("raw_auctioneer")
                    
                    similar_sales.append({
                        "year": s_yr,
                        "serial": s_ser,
                        "price": int(s_pr) if s_pr is not None else None,
                        "sold_date": str(s_dt) if s_dt else "Unknown",
                        "state": s_st if s_st else "Unknown",
                        "auctioneer": s_auc if s_auc else "Unknown"
                    })
            except Exception as e:
                print(f"Error fetching similar sales from D1: {e}")

        # Final decode pass with sales included
        decoded["similar_sales"] = similar_sales

        return Response(
            json.dumps(decoded),
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        )
