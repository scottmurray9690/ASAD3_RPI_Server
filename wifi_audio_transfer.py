import socket

# converts a file to bytes array and sends it    
def sendFile(filedata):
    print("Sending Data")
    a = conv_file(filedata)
    if(hasHeader(a)):
        sendHeader(a)
        print('Header Sent')
        # Remove the header from a
        a = a[44:]
    sendData(a,1024)
    print('Data Sent')
    #print("Done. Transmission Successful")
    return
    
def conv_file(file):    
    with open(file, "rb") as file:
        f = file.read()
        b = bytearray(f)
        return b
        
def sendHeader(a):
    a[7] = 0x00
    a[6] = 0x00
    a[5] = 0x00
    a[4] = 0x24
    client_sock.send(bytes(a[0:44]))    
    #wait()
    return
    
# check if .wav file has header
def hasHeader(arr):
    if(     arr[0] == 0x52 and  arr[1] == 0x49 
       and  arr[2] == 0x46 and  arr[3] == 0x46
       and  arr[8] == 0x57 and  arr[9] == 0x41
       and  arr[10] == 0x56 and  arr[11] == 0x45
       and  arr[12] == 0x66 and  arr[13] == 0x6D
       and  arr[14] == 0x74 and  arr[36] == 0x64
       and  arr[37] == 0x61 and  arr[38] == 0x74
       and  arr[39] == 0x61
      ):
        return True
    else:
        return False
        
    
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

    print('File sent in {} Packets'.format(packet))
    return


HOST = '192.168.50.1'
PORT = 8888

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
server_sock.bind((HOST,PORT))
server_sock.listen(1)
    
print(f"Listening for connection on {HOST}:{PORT}")
client_sock, client_info = server_sock.accept()
print("Accepted connection from ", client_info)

file_name = '/media/usb/breath.wav'

sendFile(file_name)


