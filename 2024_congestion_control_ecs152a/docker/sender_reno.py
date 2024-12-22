import socket
import time

packetSize = 1024
idSize = 4
messageSize = packetSize - idSize

with open('file.mp3', 'rb') as f:
    data = f.read()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
    udpSocket.bind(("localhost", 5000))
    udpSocket.settimeout(1)
    seqId = 0
    cwnd = 1
    ssthresh = 64
    duplicateAcks = 0
    prevAck = -1
    fastRecovery = False

    totalDelay = 0
    packetDelays = []  # delays for jitter calculation
    sentPackets = 0  # total sent packets
    totalBytes = 0  # total transmitted bytes

    startTime = time.time()  # throughput timer start

    while seqId < len(data):
        messages = []
        acks = {}

        for i in range(cwnd):
            if seqId + i * messageSize >= len(data):
                break

                # store packet 
            message = int.to_bytes(seqId + i * messageSize, idSize, byteorder='big', signed=True) + data[seqId + i * messageSize : seqId + (i + 1) * messageSize]
            messages.append((seqId + i * messageSize, message))
            acks[seqId + i * messageSize] = False

        for _, message in messages:
            udpSocket.sendto(message, ('localhost', 5001))
            sentPackets += 1  # increase sent packet count
            totalBytes += len(message)  # increase total bytes count

        while True:
            try:
                startDelayTimer = time.time()  # start delay timer
                ack, _ = udpSocket.recvfrom(packetSize)
                delayTime = time.time() - startDelayTimer  # calculate delay
                totalDelay += delayTime  #  total delay
                packetDelays.append(delayTime)  # store delay for jitter calculation

                ackId = int.from_bytes(ack[:idSize], byteorder='big')
                #print(f"Received ACK: {ackId}")

                if ackId in acks:
                    acks[ackId] = True

                if ackId > prevAck:  
                    prevAck = ackId
                    duplicateAcks = 0
                    if fastRecovery:
                        cwnd = ssthresh  # stop fast recovery
                        fastRecovery = False
                    else:
                        if cwnd < ssthresh:
                            cwnd *= 2  # begin slow start
                        else:
                            cwnd += 1  # linear
                    seqId = ackId  # window moved
                    break
                elif ackId == prevAck:  # Duplicate ACKs
                    duplicateAcks += 1
                    if duplicateAcks == 3:
                        #print("3 duplicate ACKs, fast retransmit mode")
                        udpSocket.sendto(messages[0][1], ('localhost', 5001)) 
                        ssthresh = max(1, cwnd // 2)  # ssthresh updated
                        cwnd = ssthresh + 3  # fast recovery
                        fastRecovery = True
                        break

            except socket.timeout:
                #print("Timeout occurred")
                ssthresh = max(1, cwnd // 2)  #  ssthresh updated
                cwnd = 1  # restart cwnd to 1
                seqId = prevAck + messageSize  # retransmission
                fastRecovery = False
                break

    udpSocket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))

    # throughput
    totalTime = time.time() - startTime  
    throughput = totalBytes / totalTime  
    # avg delay
    averageDelay = totalDelay / sentPackets if sentPackets > 0 else 0
    # jitter calculation
    jitters = []
    for i in range(1, len(packetDelays)):
        jitter = abs(packetDelays[i] - packetDelays[i - 1])
        jitters.append(jitter)
    # get avg jitter
    averageJitter = sum(jitters) / len(jitters) if jitters else 0
    # metric
    metric = 0.2 * (throughput / 2000) + 0.1 / (averageJitter + 1e-9) + 0.8 / (averageDelay + 1e-9)

    # print(f"total time: {totalTime:.4f} seconds")
    # print(f"throughput: {throughput:.2f} bytes/second")
    # print(f"avg delay: {averageDelay:.4f} seconds")
    # print(f"avg jitter: {averageJitter:.4f} seconds")
    # print(f"metric: {metric:.4f}")
    print(f"throughput: {throughput:.2f} bytes/second, avg delay: {averageDelay:.4f} seconds, avg jitter: {averageJitter:.4f} seconds,metric: {metric:.4f}  ")
    
