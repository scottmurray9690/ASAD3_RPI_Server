import socket
import struct, time
import os, subprocess, threading

# converts a file to bytes array and sends it    
def streamFile(fileName):
    while not os.path.isfile(fileName):
        print('file not found')
        pass
    print("Streaming file")
    with open(fileName, 'rb') as file:
        start = time.time()
        # set up header
        header = bytearray(file.read(44))
        print('got header, should be b\'RIFF\': ',header[0:4])
        # input the buffersize into the header, so app knows how much to read
        struct.pack_into('<i',header,40, bufferSize)
        time.sleep(bufferLengthSeconds) 
        #start reading and sending files
        data = file.read(bufferSize)
        while len(data) > 0:
            startsend = time.time_ns()
            client_sock.send(header)
            sendData(data,1024)
            elapsed = time.time()-start
            sendtime = (time.time_ns()-startsend)/1000000.0
            timestamp = file.tell()/4/sampleRate
            print("Timestamp: {:.3f}s,\tTime elapsed: {:.3f}s,\tTime to send: {:.3f}ms, lag: {:.0f}ms".format(timestamp,elapsed,sendtime,(elapsed-timestamp)*1000))

            time.sleep(bufferLengthSeconds- sendtime/1000) #use this if livestreaming
            data = file.read(bufferSize)
            
    return   
    
# send byte array 'a' in packets that are 'size' large         
def sendData(a, size):
    packet = 0
    start = 0
    end = size
    
    if (len(a) < size):
        client_sock.send(bytes(a))
        packet += 1
    else:
        while(end < len(a)):
            client_sock.send(bytes(a[start:end]))
            start = end
            end = (start + size)
            packet += 1
        
        client_sock.send(bytes(a[start:len(a)]))      

    #print('File sent in {} Packets'.format(packet))
    return

#variables
sampleRate = 44100
bufferLengthSeconds = 0.5
bufferSize = (int) (sampleRate*4*bufferLengthSeconds)
#Create Socket Connection
HOST = '192.168.50.1'
PORT = 8888

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
server_sock.bind((HOST,PORT))
server_sock.listen(1)
    
print(f"Listening for connection on {HOST}:{PORT}")
client_sock, client_info = server_sock.accept()
print("Accepted connection from ", client_info)

#Start Recording
directory = '/media/usb/Recording Number 1/'

if not os.path.exists(directory):
    os.mkdir(directory)

name = '15-min-block.wav'
save = directory + name 
sec = 900
rec_vars = ['arecord', '-f', 'cd', '--max-file-time', f'{sec}', save]
rec = subprocess.Popen(rec_vars, shell=False, preexec_fn=os.setsid)

#Start streaming
file_name = save

T1 = threading.Thread(target=streamFile, args=(file_name,))
T1.start()
# streamFile(file_name)


