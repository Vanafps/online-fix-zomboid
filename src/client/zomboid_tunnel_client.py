import socket
import select
import struct
import sys
import time

VPS_IP = '109.120.134.246'
TCP_PORT = 26261
HEADER_MAGIC = b'PZ'
HEADER_FORMAT = "!2sH4sHH" # Magic, UDP Port, Client IP, Client Port, Data Len
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
PLAYER_TIMEOUT = 60.0 # Clean up inactive player sockets after 60s

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def main():
    print("Starting Zomboid UDP-over-TCP Tunnel Client...")
    
    while True:
        try:
            print(f"Connecting to VPS at {VPS_IP}:{TCP_PORT}...")
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.connect((VPS_IP, TCP_PORT))
            tcp_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("Connected successfully!")
            
            # Map of (player_ip, player_port, server_port) -> (socket, last_active_time)
            player_socks = {}
            # Map of socket -> (player_ip, player_port, server_port)
            sock_players = {}
            
            running = True
            while running:
                # Prepare inputs for select
                inputs = [tcp_sock] + list(sock_players.keys())
                
                # Check for timeouts
                now = time.time()
                timed_out = []
                for key, (s, last_active) in list(player_socks.items()):
                    if now - last_active > PLAYER_TIMEOUT:
                        print(f"Player {key[0]}:{key[1]} timed out. Closing tunnel socket.")
                        s.close()
                        timed_out.append(key)
                        
                for key in timed_out:
                    s, _ = player_socks.pop(key)
                    sock_players.pop(s, None)
                
                readable, _, _ = select.select(inputs, [], [], 1.0)
                
                for sock in readable:
                    if sock == tcp_sock:
                        # Read header
                        header_data = recv_all(tcp_sock, HEADER_SIZE)
                        if not header_data:
                            print("Lost connection to VPS server.")
                            running = False
                            break
                        
                        magic, sport, ip_bytes, port_num, data_len = struct.unpack(HEADER_FORMAT, header_data)
                        if magic != HEADER_MAGIC:
                            print(f"Invalid magic: {magic}")
                            running = False
                            break
                            
                        # Read payload
                        payload = recv_all(tcp_sock, data_len)
                        if payload is None:
                            print("Failed to read payload from TCP stream")
                            running = False
                            break
                            
                        player_ip = socket.inet_ntoa(ip_bytes)
                        key = (player_ip, port_num, sport)
                        
                        # Get or create socket
                        if key not in player_socks:
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s.setblocking(False)
                            player_socks[key] = (s, now)
                            sock_players[s] = key
                            print(f"New player tunnel created: {player_ip}:{port_num} -> Local:{sport}")
                        
                        s, _ = player_socks[key]
                        player_socks[key] = (s, now) # Update activity
                        
                        # Forward payload to local Zomboid server
                        s.sendto(payload, ('127.0.0.1', sport))
                        
                    else:
                        # Data from local Zomboid server back to a player
                        try:
                            data, addr = sock.recvfrom(65535)
                            key = sock_players.get(sock)
                            if key:
                                player_ip, port_num, sport = key
                                player_socks[key] = (sock, now) # Update activity
                                
                                # Send back to VPS
                                ip_bytes = socket.inet_aton(player_ip)
                                header = struct.pack(HEADER_FORMAT, HEADER_MAGIC, sport, ip_bytes, port_num, len(data))
                                tcp_sock.sendall(header + data)
                        except Exception as e:
                            print(f"Error forwarding from local server: {e}")
                            
            # Clean up sockets on disconnect
            for s, _ in player_socks.values():
                s.close()
            tcp_sock.close()
            print("Disconnected. Reconnecting in 5 seconds...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Connection failed: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
