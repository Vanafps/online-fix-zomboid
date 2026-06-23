import urllib.request
import re
import socket
import select
import struct
import json
import os
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_page(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def get_a2s_info(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.5)
    try:
        packet = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        s.sendto(packet, (ip, port))
        r, _, _ = select.select([s], [], [], 1.5)
        if not r:
            return None
        data, addr = s.recvfrom(4096)
        if data.startswith(b'\xff\xff\xff\xffA'):
            challenge = data[5:9]
            packet = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + challenge
            s.sendto(packet, (ip, port))
            r, _, _ = select.select([s], [], [], 1.5)
            if not r:
                return None
            data, addr = s.recvfrom(4096)
        return data
    except:
        return None
    finally:
        s.close()

def parse_a2s(data):
    if not data:
        return None
    try:
        out = {}
        pos = 4
        out['header'] = chr(data[pos])
        pos += 1
        out['protocol'] = data[pos]
        pos += 1
        
        end = data.find(b'\x00', pos)
        out['name'] = data[pos:end].decode('utf-8', errors='ignore')
        pos = end + 1
        
        end = data.find(b'\x00', pos)
        out['map'] = data[pos:end].decode('utf-8', errors='ignore')
        pos = end + 1
        
        end = data.find(b'\x00', pos)
        out['folder'] = data[pos:end].decode('utf-8', errors='ignore')
        pos = end + 1
        
        end = data.find(b'\x00', pos)
        out['game'] = data[pos:end].decode('utf-8', errors='ignore')
        pos = end + 1
        
        out['appid'] = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        
        out['players'] = data[pos]
        pos += 1
        out['max_players'] = data[pos]
        pos += 1
        out['bots'] = data[pos]
        pos += 1
        out['server_type'] = chr(data[pos])
        pos += 1
        out['environment'] = chr(data[pos])
        pos += 1
        out['visibility'] = data[pos]
        pos += 1
        out['vac'] = data[pos]
        pos += 1
        
        end = data.find(b'\x00', pos)
        out['version'] = data[pos:end].decode('utf-8', errors='ignore')
        pos = end + 1
        
        out['steamid'] = 0
        out['long_appid'] = 0
        
        if pos < len(data):
            edf = data[pos]
            pos += 1
            if edf & 0x80:
                pos += 2
            if edf & 0x10:
                out['steamid'] = struct.unpack('<Q', data[pos:pos+8])[0]
                pos += 8
            if edf & 0x40:
                pos += 2
            if edf & 0x20:
                end = data.find(b'\x00', pos)
                pos = end + 1
            if edf & 0x01:
                out['long_appid'] = struct.unpack('<Q', data[pos:pos+8])[0]
                pos += 8
        return out
    except Exception as e:
        return None

# Start scraping
print("Starting pirate-friendly server scraper...")
server_ids = []

for page in range(1, 5):
    print(f"Scraping wargm list page {page}...")
    url = f"https://wargm.ru/servers/project-zomboid?page={page}"
    list_html = fetch_page(url)
    ids = re.findall(r'/server/(\d+)\?click=servers', list_html)
    server_ids.extend(ids)
    time.sleep(0.3)

server_ids = list(dict.fromkeys(server_ids))
print(f"Found {len(server_ids)} server detail links. Fetching details and filtering...")

pirate_servers = []

# Always keep our own VPS-tunneled server!
pirate_servers.append({
    "name": "My PZ Server (Aeza)",
    "ip": "109.120.134.246",
    "port": 16261
})

for idx, s_id in enumerate(server_ids):
    print(f"[{idx+1}/{len(server_ids)}] Fetching info for ID {s_id}...")
    s_url = f"https://wargm.ru/server/{s_id}"
    s_html = fetch_page(s_url)
    
    ip_port_match = re.search(r'id="copy_ip_top"[^>]*>(.*?)</span>', s_html)
    if not ip_port_match:
        continue
    ip_port = ip_port_match.group(1).strip()
    
    if ":" not in ip_port:
        continue
    ip, port_str = ip_port.split(":")
    port = int(port_str)
    
    a2s_data = get_a2s_info(ip, port)
    parsed = parse_a2s(a2s_data)
    
    if parsed:
        steamid = parsed.get("steamid", 0)
        long_appid = parsed.get("long_appid", 0)
        appid = parsed.get("appid", 0)
        
        is_pirate_friendly = (steamid == 0) or (long_appid == 480) or (appid == 480)
        
        clean_name = "".join(c if ord(c) < 128 else "?" for c in parsed['name'])
        
        if is_pirate_friendly:
            print(f" -> [KEEP] {clean_name} (SteamID: {steamid}, AppID: {long_appid or appid})")
            pirate_servers.append({
                "name": parsed["name"],
                "ip": ip,
                "port": port
            })
        else:
            print(f" -> [DROP] {clean_name} is Steam-only (SteamID: {steamid}, AppID: {long_appid or appid})")
    else:
        print(f" -> [DROP] No response from {ip}:{port}")
    
    time.sleep(0.1)

output_file = r"C:\Users\DomPC\Zomboid\Lua\servers.json"

# Backup first
if os.path.exists(output_file):
    try:
        if os.path.exists(output_file + ".old"):
            os.remove(output_file + ".old")
        os.rename(output_file, output_file + ".old")
    except:
        pass

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(pirate_servers, f, indent=2, ensure_ascii=False)

print(f"\nCompleted! Written {len(pirate_servers)} pirate-friendly servers to {output_file}.")
