import socket
import select
import struct
import sys
import time

TCP_PORT = 26261
UDP_PORTS = [16261, 16262]
HEADER_MAGIC = b'PZ'
HEADER_FORMAT = "!2sH4sHH" # Magic, UDP Port, Client IP, Client Port, Data Len
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def main():
    print("Starting Zomboid UDP-over-TCP Tunnel Server...")
    
    # Create TCP listening socket
    tcp_listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_listen.bind(('0.0.0.0', TCP_PORT))
    tcp_listen.listen(1)
    print(f"Listening for client connection on TCP port {TCP_PORT}...")
    
    while True:
        try:
            # Accept client connection
            tcp_conn, client_addr = tcp_listen.accept()
            tcp_conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Client connected from {client_addr}")
            
            # Open UDP sockets
            udp_socks = {}
            for port in UDP_PORTS:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                udp_socks[port] = s
                print(f"Listening on UDP port {port} for players...")
                
            # Run the forwarding loop
            inputs = [tcp_conn] + list(udp_socks.values())
            running = True
            
            while running:
                readable, _, _ = select.select(inputs, [], [], 1.0)
                for sock in readable:
                    if sock == tcp_conn:
                        # Read header
                        header_data = recv_all(tcp_conn, HEADER_SIZE)
                        if not header_data:
                            print("Client disconnected.")
                            running = False
                            break
                        
                        magic, port, ip_bytes, port_num, data_len = struct.unpack(HEADER_FORMAT, header_data)
                        if magic != HEADER_MAGIC:
                            print(f"Invalid magic: {magic}")
                            running = False
                            break
                            
                        # Read payload
                        payload = recv_all(tcp_conn, data_len)
                        if payload is None:
                            print("Failed to read payload from client")
                            running = False
                            break
                            
                        dest_ip = socket.inet_ntoa(ip_bytes)
                        # Send to player
                        if port in udp_socks:
                            udp_socks[port].sendto(payload, (dest_ip, port_num))
                    else:
                        # It's one of the UDP sockets
                        # Find the port number
                        src_port = None
                        for p, s in udp_socks.items():
                            if s == sock:
                                src_port = p
                                break
                        
                        data, addr = sock.recvfrom(65535)
                        ip, port_num = addr
                        ip_bytes = socket.inet_aton(ip)
                        
                        # Package and send to client over TCP
                        header = struct.pack(HEADER_FORMAT, HEADER_MAGIC, src_port, ip_bytes, port_num, len(data))
                        try:
                            tcp_conn.sendall(header + data)
                        except Exception as e:
                            print(f"Error sending to TCP client: {e}")
                            running = False
                            break
                            
            # Clean up active connection
            for s in udp_socks.values():
                s.close()
            tcp_conn.close()
            print("Sockets closed. Waiting for reconnect...")
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(2)

if __name__ == '__main__':
    main()
