import socket
import sys
import struct
# Define the IP address and port form Terminal
UDP_IP = sys.argv[1]
UDP_PORT = int(sys.argv[2])

# Create a UDP socket (AF_INET for IPv4, SOCK_DGRAM for UDP)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the address and port
sock.bind((UDP_IP, UDP_PORT))
print(f"UDP Server up and listening on {UDP_IP}:{UDP_PORT}")
buffer = 2048
while True:
    # Receive data and the client's address (buffer size is 1024 bytes)
    data, addr = sock.recvfrom(buffer)

    if data[0] == 1: #syn
        header_size = 21
        header_data = data[:header_size]
        msg_type, seq, n_len, f_size, t_packet, w_size = struct.unpack('!BIHQLH', header_data)
        file_name = data[header_size : header_size + n_len].decode('utf-8')
        print(f"Receive Handshake: File={file_name}, Size={f_size} bytes, Total Packets={t_packet}")
        ack_header = struct.pack('!BI',2,0)
        sock.sendto(ack_header, addr)
    if data[0] == 2: #ack
        
        pass
        
        


    # Optional: Send a response back to the client
    # response_message = b"Message received"
    # sock.sendto(response_message, addr)
