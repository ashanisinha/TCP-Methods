import socket
import time

packetSize = 1024
idSize = 4
messageSize = packetSize - idSize
cwnd = 1
ssthresh = 64

with open('file.mp3', 'rb') as f:
    data = f.read()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
    udpSocket.bind(("localhost", 5000))
    udpSocket.settimeout(1)

    seqId = 0
    cwnd = 1
    ssthresh = ssthresh + 1
    duplicateAcks = 0
    lastAck = -1

    totalDelay = 0
    packetDelays = []
    sentPackets = 0
    totalBytes = 0

    startTime = time.time()  # throughput time begins

    while seqId < len(data):
        messages = []
        acks = {}

        for i in range(cwnd):
            if seqId + i * messageSize >= len(data):
                break

            message = int.to_bytes(seqId + i * messageSize, idSize, byteorder='big', signed=True) + data[seqId + i * messageSize: seqId + (i + 1) * messageSize]
            messages.append((seqId + i * messageSize, message))
            acks[seqId + i * messageSize] = False

        for _, message in messages:
            udpSocket.sendto(message, ('localhost', 5001))
            sentPackets += 1
            totalBytes += len(message)

        while True:
            try:
                startDelayTimer = time.time()  # Start delay timer
                ack, _ = udpSocket.recvfrom(packetSize)
                delayTime = time.time() - startDelayTimer  # Calculate delay
                totalDelay += delayTime
                packetDelays.append(delayTime)

                ackId = int.from_bytes(ack[:idSize], byteorder='big')  # slicing of ack id. change from window code.
                #print(f"Received ACK: {ackId}")

                if ackId > lastAck:  # move congestion window
                    lastAck = ackId
                    duplicateAcks = 0
                    cwnd = cwnd + 1 if cwnd < ssthresh else cwnd + (1 // cwnd)
                    seqId = ackId 
                    break
                elif ackId == lastAck:  # checking for duplicate acks
                    duplicateAcks += 1
                    if duplicateAcks == 3:
                        #print("3 duplicate ACKs. fast retransmit mode")
                        udpSocket.sendto(messages[0][1], ('localhost', 5001))  # resend after 3 duplicate ACKs
                        ssthresh = max(1, cwnd // 2)  # recalculate ssthresh
                        cwnd = 1  # recalculate cwnd
                        break

            except socket.timeout:
                #print("Timeout")
                ssthresh = max(1, cwnd // 2)  # recalculate ssthresh after timeout
                cwnd = 1  # reset window to 1
                seqId = lastAck + messageSize  # recalculate seqId
                break

    udpSocket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))

    # throughput
    totalTime = time.time() - startTime  # total time
    throughput = totalBytes / totalTime  # bytes/second
    # avg delay
    averageDelay = totalDelay / sentPackets if sentPackets > 0 else 0
    # jitter calculation
    jitters = []
    for i in range(1, len(packetDelays)):
        jitter = abs(packetDelays[i] - packetDelays[i - 1])
        jitters.append(jitter)
    # get avg jitter
    if jitters:
        averageJitter = sum(jitters) / len(jitters)
    else:
        averageJitter = 0
    # metric
    metric = 0.2 * (throughput / 2000) + 0.1 / (averageJitter + 1e-9) + 0.8 / (averageDelay + 1e-9)

    # print(f"total time: {totalTime:.4f} seconds")
    # print(f"throughput: {throughput:.2f} bytes/second")
    # print(f"avg delay: {averageDelay:.4f} seconds")
    # print(f"avg jitter: {averageJitter:.4f} seconds")
    # print(f"metric: {metric:.4f}")
    print(f"throughput: {throughput:.2f} bytes/second, avg delay: {averageDelay:.4f} seconds, avg jitter: {averageJitter:.4f} seconds,metric: {metric:.4f}  ")

