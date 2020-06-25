# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 13:19:44 2019

@author: murta
"""

#!/usr/bin/env python3.5.3

import RPi.GPIO as GPIO
import time
import subprocess
import os
import io
import signal

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import threading 


filenum = 1
dirnum = 1
ack = False
eof_ack = False


startnstop = False
Exit = False


# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

readyLED = 5
recordLED = 6
recordBTN = 13
displayBTN = 25
audioSupplyVolt = 12

GPIO.setup(readyLED, GPIO.OUT)
GPIO.setup(recordLED, GPIO.OUT)
GPIO.setup(recordBTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(displayBTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(audioSupplyVolt, GPIO.OUT)

GPIO.output(readyLED, GPIO.LOW)
GPIO.output(recordLED, GPIO.LOW)
LEDOn = False
OLED_Rec = False
OLED_screen2 = False
usb_conn = False
unmount_ok = False
unplug = False
buttonPress = 0
file_tosend = ""
t = 0
PORT = 8888
HOST = '192.168.50.1'


# Razak & Scott Code 

# Multithreaded Python server
import socket

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
FLAG = 27
GPIO.setup(FLAG, GPIO.OUT)

GPIO.output(readyLED, GPIO.LOW)
filenum = 1
dirnum = 1
ack = False
connected = False
Exit = False
stoprecording = True
fileavail = False

# Advertise service
def listen_for_client(name_server):
    global connected, Exit
    server_sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST,PORT))
    server_sock.listen(1)
        
    print(f'Listening for connection on {HOST}:{PORT}')
    client_sock, client_info = server_sock.accept()
    connected = True
    Exit = False
    print("Accepted connection from ", client_info)
    return client_sock, server_sock


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
    
# removes .wav file header    
def removeHeader(a):
    return a[44:]

def sendHeader(a):
    print("Sending header")
    a[7] = 0x00
    a[6] = 0x00
    a[5] = 0x00
    a[4] = 0x24
    client_sock.send(bytes(a[0:44]))    
    #wait()
    return

# send byte array 'a' in packets that are 'size' large         
def sendData(a, size):
    packet = 0
    start = 0
    end = size
    if (len(a) < size):
        client_sock.send(bytes(a))
        #wait();
        packet += 1
    else:
        while(end < len(a)):
            client_sock.send(bytes(a[start:end]))
            #wait();
            start = end
            end = (start + size)
            packet += 1
        
        client_sock.send(bytes(a[start:len(a)]))
        #wait();      
    #end()
    #wait();         
    print('File sent in {} Packets'.format(packet))
    return

# TODO: Figure out what this method does
def start():
    global startnstop
    while(startnstop == False):
        pass

# sends EOF    
def end():
        global eof_ack
        print("File transmission Over")
        my_str = "END"
        end_bytes = str.encode(my_str)
        '''
        print('Waiting for EOF Ack')
        while(eof_ack == False):
            #client_sock.send(end_bytes)
            # TODO: figure out why it sleeps for 5 seconds, seems like a long time. Also the eof_ack thing is kind of useless because its a tcp connection
            time.sleep(5)
            if (eof_ack == True):
                eof_ack = False
                break
        print('EOF Ack Recieved ')
        '''

# sends files
def send():
        global FLAG, filenum,dirnum, stoprecording, fileavail, Exit, file_tosend
        print("Waiting for file")
        while (not fileavail):
            #print("Nope!")
            if Exit:
                return
            pass
        print("File Available")
        GPIO.output(FLAG, GPIO.LOW)
        fileavail=False

        my_str = "START"
        start_bytes = str.encode(my_str)
        #client_sock.send(start_bytes)

        file = file_tosend
        sendFile(file)
        #end()  This is probably useless
        filenum += 1
        return   

# converts a file to bytes array and sends it    
def sendFile(filedata):
    print("Sending Data")
    a = conv_file(filedata)
    sendHeader(a)
    print('Header Sent')
    a = removeHeader(a)
    sendData(a,1024)
    print('Data Sent')
    print("Done. Transmission Successful")
    return

# converts file to byte array
def conv_file(file):    
    with open(file, "rb") as file:
        f = file.read()
        b = bytearray(f)
        return b

# listen for user commands
def run(sock): 
    global Exit, connected
    print("Recieve thread Started")
    while connected : 
        try:
            #print("Recieving")
            data = sock.recv(1024) 
            if data == b'':
                continue
            print ("Server received data:", data)
            if data == b'Exit':
                Exit = True
                break  
            processCmd(data)
        except:
            if not connected:
                break            
    print("Recieve thread Exiting")
    return
         
# process user commands        
def processCmd(data):
        global ack, filenum, dirnum, stoprecording, eof_ack        
        print("Processing Data ", data)
        # Really don't need this "Ack" stuff
        # if data == b'\x01':
        #     print("Ack")
        #     ack = True
            
        if data == b'EOF':
            print("EOF Ack")
            eof_ack = True

        elif data == b'STARTRECORD' or data == b'\x02' or data == b'\x03':
            #start Recording
            if not LEDOn:
               start_stop_recording(60)
            stoprecording = False               
            print("Start Recording")

        elif data == b'ANALYSIS':
            #start Recording
            if not LEDOn:
               time = 6
               start_stop_recording
            (time)
            stoprecording = False            
            print("Start Recording")
            
        elif data == b'BREATH':
            #start Recording
            if not LEDOn:
               time = 15
               start_stop_recording
            (time)
            stoprecording = False               
            print("Start Recording")

        elif data == b'TIMEUP':
            #stop recording            
            if LEDOn:
               start_stop_recording
            (0)
            dirnum += 1
            filenum = 1
            stoprecording = True            
            print("Time Up")
            
        elif data == b'STOPRECORD':
            #stop recording            
            if LEDOn:
               start_stop_recording
            (0)
            dirnum += 1
            filenum = 1
            stoprecording = True            
            print("Stop Recording") 
        
        return
    

def fileAvailable():
        global filenum, dirnum, connected,fileavail, Exit, file_tosend
        filen = filenum
        
        name_curr = '/media/usb/Recording Number {}/1-min-block-{:02d}.wav'.format(dirnum,filenum)
             
        name_next = '/media/usb/Recording Number {}/1-min-block-{:02d}.wav'.format(dirnum,filenum+1)
        while connected:
            
            while(stoprecording):
                if Exit:
                    return
                pass
            
            while (not os.path.isfile(name_next) and not stoprecording):
                if Exit:
                    return
                pass

            print("File exists: ", name_next)
            print(f"Does file? {name_curr} exist? {os.path.isfile(name_curr)}")

            file_tosend = name_curr
            GPIO.output(FLAG, GPIO.HIGH)
            fileavail = True
            
            
            while(filen == filenum and fileavail):
                if Exit:
                    return
                pass
            
            name_curr = '/media/usb/Recording Number {}/1-min-block-{:02d}.wav'.format(dirnum,filenum)  
            name_next = '/media/usb/Recording Number {}/1-min-block-{:02d}.wav'.format(dirnum,filenum+1)
            filen = filenum
        print("File Available thread exiting")


def start_stop_recording(sec):
    global buttonPress, LEDOn, OLED_Rec, rec, rec_vars, directory, name, save, t

    #if not unmount_ok and not unplug:
    # TODO: improve clarity past LEDOn, probably a better boolean value than the status of the LED
    if LEDOn:
            LEDOn = False
            OLED_Rec = False
            GPIO.output(recordLED, GPIO.LOW)
            print("LED Off")
            os.killpg(rec.pid, signal.SIGTERM)
            rec.terminate()
            rec = None
    else:
            LEDOn = True
            OLED_Rec = True
            GPIO.output(recordLED, GPIO.HIGH)
            print("LED On")
            t = time.time()
            buttonPress += 1
            directory = '/media/usb/Recording Number {}/'.format(buttonPress)

            if not os.path.exists(directory):
                os.mkdir(directory)

            name = '1-min-block.wav'
            save = directory + name 
            rec_vars = ['arecord', '-f', 'cd', '--max-file-time', f'{sec}', save]
            rec = subprocess.Popen(rec_vars, shell=False, preexec_fn=os.setsid)

def my_callback(channel):
    start_stop_recording(60)
       

def my_callback2(channel):
    global OLED_buttonPress, OLED_screen2, unmount_ok

    start_timer = time.time()

    while GPIO.input(channel) == 0: #wait for button press
        pass

    buttonTime = time.time() - start_timer 

    if .1 <= buttonTime < 2:
        if OLED_screen2:
            OLED_screen2 = False
         
        else:
            OLED_screen2 = True

    elif buttonTime >= 2 and not LEDOn:
        if not unmount_ok:
            unmount_cmd = "sudo umount /media/usb"
            os.system(unmount_cmd)
            unmount_ok = True
           
            
def main_thread(client_sock, server_sock):
    global startnstop,connected
    if connected:    
            t1 = threading.Thread(target=run, args=(client_sock,))
            #Checks if file is available
            t2 = threading.Thread(target=fileAvailable)

            # starting thread 1 and 2
            t1.start()
            t2.start()
            try:
                #print("Sending F5.wav")
                while not Exit:
                    send()
                    pass
                print("Closing socket")     
                connected = False
                startnstop = False
                client_sock.close()
                server_sock.close()
                t1.join()
                t2.join()
            except Exception as e:
                print("Error Sending File: ", e)
                connected = False
                startnstop = False
                client_sock.close()
                server_sock.close()
                t1.join()
                t2.join()
            
            print("Main Exiting")



     
GPIO.add_event_detect(recordBTN, GPIO.BOTH, callback=my_callback, bouncetime=500)
GPIO.add_event_detect(displayBTN, GPIO.BOTH, callback=my_callback2, bouncetime=500)
      
   
while True:
    
       if not startnstop:
           print("In Jeffs Code")
           client_sock, server_sock = listen_for_client("Rpi_zero_server")
           T1 = threading.Thread(target=main_thread, args=(client_sock,server_sock,))
           T1.start()
           startnstop = True
           
       usb_stats = subprocess.getoutput("ls -l /dev/disk/by-uuid/")
           
       # Draw a black filled box to clear the image.
       draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
       hours, rem =divmod(time.time() - t, 3600)
       minutes, seconds = divmod(rem, 60)
    
       dur = "  Duration: {:0>2}:{:0>2}:{:0>2}".format(int(hours), int(minutes), round(seconds))
       direc = "  Recording Number {}".format(buttonPress)
    
       if 'C6FA-6FD7' in usb_stats:
           if not os.path.ismount('/media/usb'):
               mount_cmd = "sudo mount /dev/sda1 /media/usb -o uid=pi,gid=pi"
               os.system(mount_cmd)
           usb_conn = True
           if unplug:
               unplug = False
               unmount_ok = False
       else:
           usb_conn = False
           unplug = True
    
       if not OLED_screen2:
           if OLED_Rec:
               draw.text((x, top+0), "  Recording Audio...", font=font, fill=255)
               draw.text((x, top+15), direc, font=font, fill=255)
               draw.text((x, top+24), dur, font=font, fill=255)
               
           else:
               if usb_conn:
                  #draw.text((x, top+0), " U of M BME Prototype", font=font, fill=255)
                  draw.text((x, top+0), "  Recording Stopped", font=font, fill=255)
        
                  if not unmount_ok:
                      GPIO.output(readyLED, GPIO.HIGH)
                      GPIO.output(audioSupplyVolt, GPIO.HIGH)
                      draw.text((x, top+16), "    USB Mounted OK", font=font, fill=255)
                      draw.text((x, top+24), "  **Do NOT Remove!**", font=font, fill=255)
                  else:
                      GPIO.output(readyLED, GPIO.LOW)
                      GPIO.output(audioSupplyVolt, GPIO.LOW)
                      if os.path.ismount('/media/usb'):
                          umount_cmd = "sudo umount /dev/sda1 /media/usb"
                          os.system(umount_cmd)
                      draw.text((x, top+16), "    USB Un-Mounted", font=font, fill=255)
                      draw.text((x, top+24), " **OK to remove USB**", font=font, fill=255)
                  
               if not usb_conn:
                  GPIO.output(readyLED, GPIO.LOW)
                  GPIO.output(audioSupplyVolt, GPIO.LOW)
                  draw.text((x, top+0), "    ***ERROR!***", font=font, fill=255)
                  draw.text((x, top+16), " USB Drive NOT found", font=font, fill=255)
                  draw.text((x, top+24), "  Please insert USB", font=font, fill=255)
       else:
           cmd = "free -m | awk 'NR==2{printf \"Mem: %d/%d MB   %d%%\", $3,$2,$3*100/$2}'"
           MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
           cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%d GB      %s\", $3,$2,$5}'"
           Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
    
           temp_read = open("/sys/class/thermal/thermal_zone0/temp", "r")
           temp_raw = float(temp_read.readline ())
           temperature = temp_raw/1000
    
           temp_message = "Temperature:   {:.1f}'C".format(temperature)
    
           draw.text((x, top+0), "Device Stats:", font=font, fill=255)
           draw.text((x, top+8), MemUsage, font=font, fill=255)
           draw.text((x, top+16), Disk, font=font, fill=255)
           draw.text((x, top+24), temp_message, font=font, fill=255)
    
       # Display image.
       disp.image(image)
       disp.show()
       
       time.sleep(1)
         
T1.join()
