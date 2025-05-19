# udp_nmea_sender.py

import socket
import time

def read_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f if line.strip()]

def send_lines_udp(lines, host, port, delay_ms):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for line in lines:
        sock.sendto(line.encode(), (host, port))
        time.sleep(delay_ms / 1000.0)  # convert ms to seconds
    sock.close()

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 5:
        print("Usage: python udp_nmea_sender.py <file> <host> <port> <delay_ms>")
    else:
        file = sys.argv[1]
        host = sys.argv[2]
        port = int(sys.argv[3])
        delay_ms = int(sys.argv[4])

        lines = read_lines(file)
        send_lines_udp(lines, host, port, delay_ms)
