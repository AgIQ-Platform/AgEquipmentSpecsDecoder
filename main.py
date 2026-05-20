import re
import json
from workers import WorkerEntrypoint, Response
from parser import decode_serial, normalize_cat_serial

def get_field(row, field, default=None):
    """
    Bulletproof helper to extract fields from database rows,
    supporting dictionaries, JS proxy objects, and object attributes safely.
    """
    if row is None:
        return default
    # 1. Try dict/item access
    try:
        val = row[field]
        if val is not None:
            # Handle Pyodide/JS string objects by converting to standard python strings
            return str(val) if isinstance(val, (str, int, float)) else val
    except Exception:
        pass
    # 2. Try attribute access
    try:
        val = getattr(row, field, None)
        if val is not None:
            return str(val) if isinstance(val, (str, int, float)) else val
    except Exception:
        pass
    return default

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        try:
            return await self._handle_fetch(request)
        except Exception as e:
            import traceback
            error_details = {
                "error": "Unhandled Exception in Worker",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            return Response(
                json.dumps(error_details),
                status=500,
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )

    async def _handle_fetch(self, request):
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
                    r_company = get_field(wmc_res, "company", "Unknown")
                    r_country = get_field(wmc_res, "country_code", "Unknown")
                    r_make = get_field(wmc_res, "make_key", "unknown")
                    
                    wmc_info = {
                        "company": r_company.strip(),
                        "country": r_country.strip(),
                        "make_key": r_make.strip()
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
                    if cat_res and cat_res.results:
                        for r in cat_res.results:
                            r_key = get_field(r, "make_model_key")
                            r_year = get_field(r, "year")
                            r_start = get_field(r, "serial_start")
                            r_conf = get_field(r, "confidence")
                            
                            if not r_start:
                                continue
                                
                            r_prefix, r_seq = normalize_cat_serial(r_start)
                            if r_prefix == input_prefix:
                                if input_seq >= r_seq:
                                    if best_cat is None or r_seq > best_cat["r_seq"]:
                                        best_cat = {
                                            "make_model_key": r_key,
                                            "year": int(r_year) if r_year else None,
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
                    
                if range_res and range_res.results:
                    for r in range_res.results:
                        r_key = get_field(r, "make_model_key")
                        r_year = get_field(r, "year")
                        r_start = get_field(r, "serial_start")
                        r_conf = get_field(r, "confidence")
                        
                        if not r_start:
                            continue
                        clean_start = r_start.strip().upper()
                        if serial_clean >= clean_start:
                            best_match = {
                                "make_model_key": r_key,
                                "year": int(r_year) if r_year else None,
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
                    if jd_res and jd_res.results:
                        for r in jd_res.results:
                            r_yr = get_field(r, "year")
                            r_start = get_field(r, "serial_start")
                            r_conf = get_field(r, "confidence")
                            jd_seq_ranges.append((int(r_yr) if r_yr else None, r_start, r_conf))
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
                if sales_res and sales_res.results:
                    for s in sales_res.results:
                        s_yr = get_field(s, "year")
                        s_ser = get_field(s, "serial_number")
                        s_pr = get_field(s, "price")
                        s_dt = get_field(s, "sold_date", "Unknown")
                        s_st = get_field(s, "state_code", "Unknown")
                        s_auc = get_field(s, "raw_auctioneer", "Unknown")
                        
                        similar_sales.append({
                            "year": int(s_yr) if s_yr else None,
                            "serial": s_ser,
                            "price": int(s_pr) if s_pr is not None else None,
                            "sold_date": s_dt,
                            "state": s_st,
                            "auctioneer": s_auc
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
