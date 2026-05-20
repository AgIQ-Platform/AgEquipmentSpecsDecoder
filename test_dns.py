import socket

hosts_to_try = [
    "dpg-d7egkdnlk1mc73fclhrg-b.oregon-postgres.render.com",
    "dpg-d7egkdnlk1mc73fclhrg-b.singapore-postgres.render.com",
    "dpg-d7egkdnlk1mc73fclhrg-b.frankfurt-postgres.render.com",
    "dpg-d7egkdnlk1mc73fclhrg-b.ohio-postgres.render.com",
]

for host in hosts_to_try:
    try:
        ip = socket.gethostbyname(host)
        print(f"SUCCESS: {host} resolved to {ip}")
    except socket.gaierror as e:
        print(f"FAILED: {host} - {e}")
