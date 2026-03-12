import socket
import sys
import os
import struct
import math
MESSAGE_ADDR = sys.argv[1]
UDP_IP = sys.argv[2]
UDP_PORT = int(sys.argv[3])
print(MESSAGE_ADDR,UDP_IP,UDP_PORT)
print(f"UDP target IP: {UDP_IP}")
print(f"UDP target port: {UDP_PORT}")
chunk_size = 1460

#Create Header For Hand shake

def create_handshake_packet(MESSAGE_ADDR,chunk_size = 1460):
    file_name = os.path.basename(MESSAGE_ADDR).encode('utf-8')
    file_size = os.path.getsize(MESSAGE_ADDR)
    name_len = len(file_name)
    
    total_packet = math.ceil(file_size/chunk_size)
    # Create HandShake Packet --------------------------------
    # B(1) + I(4) + H(2) + Q(8) +L(4) +H(2)= 21 bytes
    # Type(1), Seq(4), NameLen(2), FileSize(8), TotalPackets(4), WinSize(2)
    #type {1:syn,2:ack,3:fin}}
    msg_type = 1
    seq = 0
    header = struct.pack('!BIHQLH',
                        msg_type,
                        seq,
                        name_len,
                        file_size,
                        total_packet,
                        64)
    return header+file_name

def sending_file_rdt(sock:socket.socket,file_addr,total_packets,server_addr,win_size=64,chunk_size = 1460):
    base = 1 #left border of window
    next_seq_num = 1 #count next_seq as 1 amount of packet not size as TCP
    packets_data = {}
    with open(file_addr, 'rb') as f:
        while base <= total_packets:
            while next_seq_num < base + win_size and next_seq_num <= total_packets:
                if next_seq_num not in packets_data:
                    chunk = f.read(chunk_size)
                    # Type 2 = ACK
                    header = struct.pack('!BI', 2, next_seq_num)
                    packets_data[next_seq_num] = header + chunk
                    print(packets_data)
                    
                
                sock.sendto(packets_data[next_seq_num], server_addr)
                print(f"Sent Packet #{next_seq_num}")
                next_seq_num += 1
                #รอรับ ack ตอบกลับเพื่ออัพเดต base
            try:
                sock.settimeout(0.5)
                ack_data, _ = sock.recvfrom(1024) #packet only have header
                ack_type,ack_seq = struct.unpack('!BI',ack_data)
                if ack_type == 2:
                    if ack_seq >= base:
                        for i in range(base, ack_seq + 1):
                            if i in packets_data: del packets_data[i]
                        base = ack_seq + 1 #server sent same seq num and client have to known that you have to sent next seq na, it easy to under stand but not standard  for tcp 
                        print(f"ACK received up to #{ack_seq}, Base is now {base}")
                    
                    pass
                if ack_type == 3:
                    fin = struct.pack('B',3)
                    sock.send(fin,server_addr)
                    return
                pass
            except socket.timeout:
                pass
            
            
            
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0) #set timeout
print("Starting Handshake...")
while True:
    try:   
        packet = create_handshake_packet(MESSAGE_ADDR,chunk_size)
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        resp, addr = sock.recvfrom(1024)
        msg_type,next_seq = struct.unpack('!BI',resp)
        if msg_type == 2 and next_seq == 0:
            file_name = os.path.basename(MESSAGE_ADDR).encode('utf-8')
            file_size = os.path.getsize(MESSAGE_ADDR)
            name_len = len(file_name)
            total_packet = math.ceil(file_size/chunk_size)

            print("Handshake Success! Server is ready.")
            sending_file_rdt(MESSAGE_ADDR,total_packet,UDP_IP,64,1460)
            break
    except socket.timeout:
        print("Timeout! Retransmitting Handshake...")
        continue
sending_file_rdt
#Start Sending Files
print(f"Sent UDP packet to {UDP_IP}:{UDP_PORT}: HEADER")

# Optional: Receive a response from the server
data, addr = sock.recvfrom(1024)
msg_type,next_seq = struct.unpack('!BI',data)
print(f"Received response: {next_seq} from {addr}")
sock.close()
