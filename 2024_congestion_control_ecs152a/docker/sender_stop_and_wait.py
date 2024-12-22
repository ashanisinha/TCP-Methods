import socket
import time

packetSize = 1024
idSize = 4
messageSize = packetSize - idSize

with open('file.mp3', 'rb') as f:  # read file
    data = f.read()

# create udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
    startTime = time.time()  # throughput times begins
    
    udpSocket.bind(("0.0.0.0", 5000)) 
    udpSocket.settimeout(1)

    seqId = 0
    totalDelay = 0
    packetDelays = []  #  delays jitter calculation
    sentPackets = 0
    totalBytes = 0

    while seqId < len(data):  # start data sending
        startDelayTimer = time.time()  # Start packet delay
        message = int.to_bytes(seqId, idSize, byteorder='big', signed=True) + data[seqId : seqId + messageSize]
        udpSocket.sendto(message, ('localhost', 5001)) 
        sentPackets += 1 # increase packets being sent
        totalBytes += len(message)

        while True:  # wait for acknowledgement
            try: 
                ack, _ = udpSocket.recvfrom(packetSize)
                delayTime = time.time() - startDelayTimer  # Calculate delay
                totalDelay += delayTime
                packetDelays.append(delayTime)  # add packet delay
                #print(f"Delay time, seqId {seqId}: {delayTime:.4f} seconds") # cout delay time

                # extract id
                ackId = int.from_bytes(ack[:idSize], byteorder='big', signed=True)
                #print(f"Received ACK,  seqId: {ackId}") 

                # set sequence id to acknowledgement id
                if ackId > seqId:
                    seqId = ackId 
                    break
            except socket.timeout:  # resend if timeout, no ack received
               # print(f"Timeout, seqId: {seqId}, resending packet")
                udpSocket.sendto(message, ('localhost', 5001))

    # closing message
    udpSocket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))

    # throughput
    totalTime = time.time() - startTime  # total time
    throughput = totalBytes / totalTime  # bytes/second
    # avg delay
    averageDelay = totalDelay / sentPackets if sentPackets > 0 else 0
    #  jitter calcs
    jitters = []
    for i in range(1, len(packetDelays)):
        jitter = abs(packetDelays[i] - packetDelays[i - 1])
        jitters.append(jitter)
    # get avg jitter
    if jitters:
        averageJitter = sum(jitters) / len(jitters)
    else:
        averageJitter = 0
    #  metric
    metric = 0.2 * (throughput / 2000) + 0.1 / (averageJitter + 1e-9) + 0.8 / (averageDelay + 1e-9)

    # print(f"total time: {totalTime:.4f} seconds")
    # print(f"throughput: {throughput:.2f} bytes/second")
    # print(f"avg delay: {averageDelay:.4f} seconds")
    # print(f"avg jitter: {averageJitter:.4f} seconds")
    # print(f"metric: {metric:.4f}")
    print(f"throughput: {throughput:.2f} bytes/second, avg delay: {averageDelay:.4f} seconds, avg jitter: {averageJitter:.4f} seconds,metric: {metric:.4f}  ")
    
