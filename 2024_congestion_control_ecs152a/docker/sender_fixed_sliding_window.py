import socket
import time

packetSize = 1024
idSize = 4
messageSize = packetSize - idSize
window = 100  # keep window size big

with open('file.mp3', 'rb') as f:
    data = f.read()  # read data

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:  # socket
    udpSocket.bind(("localhost", 5000))
    udpSocket.settimeout(1)

    seqId = 0
    totalDelay = 0
    packetDelays = []  # delays for jitter calculation
    sentPackets = 0
    totalBytes = 0

    startTime = time.time()  # throughput time begins

    while seqId < len(data):  # start data sending
        messages = []
        for i in range(window):
            if seqId + i * messageSize >= len(data):
                break
            message = int.to_bytes(seqId + i * messageSize, idSize, byteorder='big', signed=True) + \
                      data[seqId + i * messageSize: seqId + (i + 1) * messageSize]
            messages.append((seqId + i * messageSize, message))

        for _, message in messages:
            udpSocket.sendto(message, ('localhost', 5001))
            sentPackets += 1  # count sent packets
            totalBytes += len(message)

        while True:  # wait for acknowledgement
            try:
                startDelayTimer = time.time()  # Start packet delay
                ack, _ = udpSocket.recvfrom(packetSize)
                delayTime = time.time() - startDelayTimer  # Calculate delay
                totalDelay += delayTime
                packetDelays.append(delayTime)  # add packet delay

                # extract id
                ackId = int.from_bytes(ack[:idSize], byteorder='big')
                #print(f"Received ACK: {ackId}")

                # set sequence id to acknowledgment id
                if ackId > seqId:
                    seqId = ackId
                    break

            except socket.timeout:
                #print("Timeout. Resending Now")
                for sid, message in messages:
                    if sid >= seqId:
                        #print(f"Resending packet {sid}")
                        udpSocket.sendto(message, ('localhost', 5001))

    udpSocket.sendto(int.to_bytes(-1, idSize, signed=True, byteorder='big'), ('localhost', 5001))

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

     #print(f"total time: {totalTime:.4f} seconds")
    print(f"throughput: {throughput:.2f} bytes/second, avg delay: {averageDelay:.4f} seconds, avg jitter: {averageJitter:.4f} seconds,metric: {metric:.4f}  ")
     #print(f"avg delay: {averageDelay:.4f} seconds")
    #  print(f"avg jitter: {averageJitter:.4f} seconds")
    #  print(f"metric: {metric:.4f}")