import socket
import struct
import os
import time

def send_file_gbn(file_path, server_addr, sock, win_size, total_packets):
    CHUNK_SIZE = 1400
    base = 1
    next_seq_num = 1
    packets_data = {} # เก็บข้อมูล packet ไว้เผื่อต้องส่งใหม่ (Retransmit)
    
    # อ่านไฟล์ทั้งหมดเก็บเข้า Memory (เฉพาะที่จำเป็น หรืออ่านทีละนิด)
    with open(file_path, 'rb') as f:
        # วนลูปจนกว่าจะส่งครบและได้รับ ACK ครบทุก packet
        while base <= total_packets:
            
            # 1. ส่งข้อมูลให้เต็ม Window
            while next_seq_num < base + win_size and next_seq_num <= total_packets:
                if next_seq_num not in packets_data:
                    data = f.read(CHUNK_SIZE)
                    # Type 2 = Data
                    header = struct.pack('!BI', 2, next_seq_num)
                    packets_data[next_seq_num] = header + data
                
                sock.sendto(packets_data[next_seq_num], server_addr)
                print(f"Sent Packet #{next_seq_num}")
                next_seq_num += 1

            # 2. รอรับ ACK พร้อม Timeout
            try:
                sock.settimeout(0.5) # ปรับตาม RTT ของโจทย์ (เช่น 0.1 - 0.5)
                ack_data, _ = sock.recvfrom(1024)
                ack_type, ack_seq = struct.unpack('!BI', ack_data[:5])
                
                if ack_type == 2:
                    # GBN ใช้ Cumulative ACK: ถ้าได้ ACK 5 หมายถึง 1-5 ถึงชัวร์
                    if ack_seq >= base:
                        # ลบข้อมูลที่ได้รับ ACK แล้วออกจากบัฟเฟอร์เพื่อประหยัดแรม
                        for i in range(base, ack_seq + 1):
                            if i in packets_data: del packets_data[i]
                        base = ack_seq + 1
                        print(f"ACK received up to #{ack_seq}, Base is now {base}")

            except socket.timeout:
                # 3. เกิด Timeout: ส่งใหม่ทั้งหมดใน Window ตั้งแต่ base
                print(f"Timeout! Resending from Packet #{base}")
                for i in range(base, next_seq_num):
                    sock.sendto(packets_data[i], server_addr)

    # 4. ส่ง FIN (Type 3) เพื่อจบการทำงาน
    fin_packet = struct.pack('!BI', 3, next_seq_num)
    sock.sendto(fin_packet, server_addr)