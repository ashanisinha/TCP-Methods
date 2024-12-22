import socket
import time

#Change the chat code

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
INITIAL_CWND = 1
INITIAL_SSTHRESH = 50

with open('send.txt', 'rb') as f:
    data = f.read()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    #change variable names and order os somt things
    seq_id = 0
    cwnd = 1
    ssthresh = 50
    duplicate_acks = 0
    last_ack = -1
    fast_recovery = False

    while seq_id < len(data):
        messages = []
        acks = {}

        for i in range(cwnd):
            if seq_id + i * MESSAGE_SIZE >= len(data):
                break

            message = int.to_bytes(seq_id + i * MESSAGE_SIZE, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id + i * MESSAGE_SIZE : seq_id + (i + 1) * MESSAGE_SIZE]
            messages.append((seq_id + i * MESSAGE_SIZE, message))
            acks[seq_id + i * MESSAGE_SIZE] = False

        for _, message in messages:
            udp_socket.sendto(message, ('localhost', 5001))

        while True:
            try:
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(f"Received ACK for seq_id: {ack_id}")

                if ack_id in acks:
                    acks[ack_id] = True

                if ack_id == last_ack:
                    duplicate_acks += 1
                    if duplicate_acks == 3:
                        print("3 duplicate ACKs received, performing fast retransmit")
                        udp_socket.sendto(messages[0][1], ('localhost', 5001))
                        ssthresh = max(1, cwnd // 2)
                        cwnd = max(1, cwnd // 2)
                        fast_recovery = True
                        break
                else:
                    duplicate_acks = 0
                    last_ack = ack_id
                    if fast_recovery:
                        # Exit fast recovery
                        cwnd = ssthresh
                        fast_recovery = False

                if all(acks.values()):
                    if cwnd < ssthresh:
                        cwnd *= 2
                    else:
                        cwnd += 1
                    seq_id += MESSAGE_SIZE * len(messages)
                    break

            except socket.timeout:
                print("Timeout occurred, reducing ssthresh and resetting cwnd")
                ssthresh = max(1, cwnd // 2)
                cwnd = 1
                fast_recovery = False
                break

    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
