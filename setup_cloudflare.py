import os
import sys
import json
import urllib.request
import urllib.error

CLOUDFLARE_API_KEY = "cfat_fjZZwEx1rVLs3vqtRVmd2GOOn6G0WkC1VZGkSF3n4efa1418"
CLOUDFLARE_ACCOUNT_ID = "50c2630c0b2ac308a672a1104f51c6f2"

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
    print("=== CLOUDFLARE API DIAGNOSTICS ===")
    
    # 1. Fetch Zones (Domains)
    print("Fetching active zones/domains under your Cloudflare account...")
    zones_url = "https://api.cloudflare.com/client/v4/zones"
    zones_res = cf_api_request(zones_url)
    
    if not zones_res or not zones_res.get("success"):
        print("Failed to authenticate or fetch zones. Check your API token.")
        return
        
    zones = zones_res.get("result", [])
    if not zones:
        print("No active domains found in this Cloudflare account. Please add a domain first.")
        return
        
    print(f"Found {len(zones)} domains:")
    for idx, z in enumerate(zones):
        print(f" [{idx}] {z['name']} (ID: {z['id']})")
        
    # Select the first zone or look for dpa.auction
    selected_zone = None
    for z in zones:
        if z["name"] == "dpa.auction" or "auction" in z["name"]:
            selected_zone = z
            break
            
    if not selected_zone:
        selected_zone = zones[0]
        
    print(f"\nTargeting domain: {selected_zone['name']}")
    
    # 2. Check for existing 'ag-decoder' tunnel
    print("Checking for existing 'ag-decoder' tunnels...")
    tunnels_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel"
    tunnels_res = cf_api_request(tunnels_url)
    
    tunnel_id = None
    tunnel_token = None
    
    if tunnels_res and tunnels_res.get("success"):
        tunnels = tunnels_res.get("result", [])
        for t in tunnels:
            if t["name"] == "ag-decoder":
                print(f"Found existing tunnel 'ag-decoder' (ID: {t['id']})")
                tunnel_id = t["id"]
                break
                
    # 3. Create tunnel if not exists
    if not tunnel_id:
        print("Creating a new Cloudflare Tunnel named 'ag-decoder'...")
        create_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel"
        # We also need to supply a dummy secret for local run or use system source
        create_data = {
            "name": "ag-decoder",
            "config_src": "cloudflare"
        }
        create_res = cf_api_request(create_url, method="POST", data=create_data)
        if create_res and create_res.get("success"):
            result = create_res.get("result", {})
            tunnel_id = result.get("id")
            print(f"Successfully created tunnel! ID: {tunnel_id}")
        else:
            print("Failed to create tunnel.")
            return
            
    # 4. Fetch tunnel token
    print(f"Retrieving Tunnel Token for ID {tunnel_id}...")
    token_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel/{tunnel_id}/token"
    token_res = cf_api_request(token_url)
    if token_res and token_res.get("success"):
        tunnel_token = token_res.get("result")
        print("Tunnel Token retrieved successfully.")
    else:
        print("Failed to retrieve tunnel token.")
        return
        
    # 5. Add DNS CNAME Record
    subdomain = "decoder"
    full_hostname = f"{subdomain}.{selected_zone['name']}"
    print(f"Configuring DNS CNAME record for {full_hostname} pointing to tunnel...")
    
    # Check if DNS record already exists
    dns_url = f"https://api.cloudflare.com/client/v4/zones/{selected_zone['id']}/dns_records?name={full_hostname}"
    dns_res = cf_api_request(dns_url)
    
    dns_id = None
    if dns_res and dns_res.get("success"):
        records = dns_res.get("result", [])
        if records:
            dns_id = records[0]["id"]
            print(f"Found existing DNS record (ID: {dns_id})")
            
    dns_data = {
        "type": "CNAME",
        "name": subdomain,
        "content": f"{tunnel_id}.cfargotunnel.com",
        "ttl": 1, # Automatic
        "proxied": True
    }
    
    if dns_id:
        # Update existing
        update_url = f"https://api.cloudflare.com/client/v4/zones/{selected_zone['id']}/dns_records/{dns_id}"
        dns_save_res = cf_api_request(update_url, method="PUT", data=dns_data)
    else:
        # Create new
        create_dns_url = f"https://api.cloudflare.com/client/v4/zones/{selected_zone['id']}/dns_records"
        dns_save_res = cf_api_request(create_dns_url, method="POST", data=dns_data)
        
    if dns_save_res and dns_save_res.get("success"):
        print(f"DNS CNAME record configured successfully: {full_hostname} -> {tunnel_id}.cfargotunnel.com")
    else:
        print("Failed to configure DNS CNAME record.")
        return
        
    # 6. Configure Tunnel Routing (Routes traffic from hostname to localhost:5001)
    print("Configuring tunnel ingress rules...")
    config_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel/{tunnel_id}/configurations"
    config_data = {
        "config": {
            "ingress": [
                {
                    "hostname": full_hostname,
                    "service": "http://localhost:5001"
                },
                {
                    "service": "http_status:404"
                }
            ]
        }
    }
    config_res = cf_api_request(config_url, method="PUT", data=config_data)
    if config_res and config_res.get("success"):
        print("Tunnel ingress configuration updated successfully.")
    else:
        print("Failed to update tunnel configuration. (Note: You might need to configure it in Cloudflare Zero Trust dashboard, but we'll try running the tunnel).")
        
    # Output the credentials for wrangler/cloudflared running
    output = {
        "tunnel_id": tunnel_id,
        "tunnel_token": tunnel_token,
        "hostname": full_hostname
    }
    
    with open("cloudflare_tunnel_details.json", "w") as out:
        json.dump(output, out, indent=2)
        
    print("\n=========================================")
    print("SUCCESS: Cloudflare Tunnel Details Saved!")
    print(f"  Live Domain URL: https://{full_hostname}")
    print(f"  Tunnel Token: {tunnel_token[:15]}...")
    print("=========================================")

if __name__ == "__main__":
    main()
