import json
import urllib.request
import urllib.error

CLOUDFLARE_API_KEY = "cfat_fjZZwEx1rVLs3vqtRVmd2GOOn6G0WkC1VZGkSF3n4efa1418"
CLOUDFLARE_ACCOUNT_ID = "50c2630c0b2ac308a672a1104f51c6f2"
ZONE_ID = "6a9368ecd1d52286507ffc0a0f2ceb1c" # agequipmentspecs.com

def cf_api_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {err_msg}")
        return None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def main():
    print("=== DPA CLOUDFLARE DNS CONFIGURATOR ===")
    
    subdomain = "decoder"
    full_hostname = f"{subdomain}.agequipmentspecs.com"
    target_cname = "dpa-decoder-unique-2026.loca.lt"
    
    print(f"Configuring DNS CNAME record: {full_hostname} -> {target_cname}")
    
    # 1. Search for existing CNAME record for 'decoder'
    search_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name={full_hostname}"
    search_res = cf_api_request(search_url)
    
    dns_id = None
    if search_res and search_res.get("success"):
        records = search_res.get("result", [])
        if records:
            dns_id = records[0]["id"]
            print(f"Found existing DNS record (ID: {dns_id})")
            
    dns_data = {
        "type": "CNAME",
        "name": subdomain,
        "content": target_cname,
        "ttl": 1, # Automatic
        "proxied": True # Route through Cloudflare proxy
    }
    
    # 2. Update or Create the CNAME record
    if dns_id:
        print(f"Updating existing CNAME record (ID: {dns_id})...")
        save_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{dns_id}"
        save_res = cf_api_request(save_url, method="PUT", data=dns_data)
    else:
        print("Creating a new CNAME record...")
        save_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
        save_res = cf_api_request(save_url, method="POST", data=dns_data)
        
    if save_res and save_res.get("success"):
        print("\n=========================================")
        print("SUCCESS: Branded Live DNS Configured!")
        print(f"  Branded URL: https://{full_hostname}")
        print(f"  Pointing to CNAME: {target_cname}")
        print("=========================================")
    else:
        print("Failed to configure CNAME record in your Cloudflare account. Please check token DNS edit permissions.")

if __name__ == "__main__":
    main()
