#!/usr/bin/env python3.5.3

import RPi.GPIO as GPIO
import time, struct
import subprocess, threading
from subprocess import call
import os
import io
import signal
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306
import phone_comm

# Raspberry Pi pin configuration:
RST = 24

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

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

# Display Splash Screen 1
image = Image.open('/home/pi/Python/splash_b_bkgnd.png').convert('1')

# Display image.
disp.image(image)
disp.display()
time.sleep(2.5)

# Clear display.
disp.clear()
disp.display()

# Display Splash Screen 2
image = Image.open('/home/pi/Python/ss2.png').convert('1')

# Display image.
disp.image(image)
disp.display()
time.sleep(5)

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

readyLED = 5
recordLED = 6
recordBTN = 13
displayBTN = 26
usbBTN = 25
audioSupplyVolt = 12

GPIO.setup(readyLED, GPIO.OUT)
GPIO.setup(recordLED, GPIO.OUT)
GPIO.setup(recordBTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(displayBTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(usbBTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(audioSupplyVolt, GPIO.OUT)

GPIO.output(readyLED, GPIO.LOW)
GPIO.output(recordLED, GPIO.LOW)
LEDOn = False
OLED_Rec = False
OLED_main = True
OLED_screen2 = False
OLED_screen3 = False
OLED_screen4 = False
OLED_screen5 = False
loop_back = False
usb_conn = False
unmount_ok = False
unplug = False
buttonPress = 0
t = 0
mic_gain = 9
call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)])

# Called when record button pressed
def my_callback(channel):
    global buttonPress, LEDOn, OLED_Rec, rec, rec_vars, directory, name, save, t

    if not unmount_ok and not unplug:
        if LEDOn:
            LEDOn = False
            OLED_Rec = False
            GPIO.output(recordLED, GPIO.LOW)
            os.killpg(rec.pid, signal.SIGTERM)
            rec.terminate()
            rec = None
        else:
            LEDOn = True
            OLED_Rec = True
            GPIO.output(recordLED, GPIO.HIGH)
            t = time.time()
            buttonPress += 1
            directory = '/media/usb/Recording Number {}/'.format(buttonPress)

            if not os.path.exists(directory):
                os.mkdir(directory)

            name = '15-min-block.wav'
            save = directory + name
            rec_vars = ['arecord', '-f', 'cd', '--max-file-time', '900', save]
            rec = subprocess.Popen(rec_vars, shell=False, preexec_fn=os.setsid)

# Called when screen change button pressed
def my_callback2(channel):
    global displayBTN_press, usb_conn, OLED_main, OLED_screen2, OLED_screen3, OLED_screen4, OLED_screen5, loop_back, mic_gain

    start_timer1 = time.time()

    while GPIO.input(channel) == 0: #wait for button press
        pass

    buttonTime1 = time.time() - start_timer1

    if buttonTime1 >= 1 and usb_conn:
        if OLED_screen5:
            OLED_screen5 = False
            loop_back = True

        if OLED_screen4:
            OLED_screen4 = False
            OLED_screen5 = True

        if OLED_screen3:
            OLED_screen3 = False
            OLED_screen4 = True

        if OLED_screen2:
            OLED_screen2 = False
            OLED_screen3 = True

        if OLED_main:
            OLED_main = False
            OLED_screen2 = True
            loop_back = False

        if loop_back:
            OLED_main = True

    if .1 <= buttonTime1 < 1 and OLED_screen3:
        if mic_gain < 15:
            mic_gain += 1
            call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)])

# Called when unmount button pressed
def my_callback3(channel):
    global usbBTN_press, LEDOn, unmount_ok, S3, OLED_screen5, mic_gain

    start_timer2 = time.time()

    while GPIO.input(channel) == 0: #wait for button press
        pass

    buttonTime2 = time.time() - start_timer2

    if .1 <= buttonTime2 < 2 and OLED_screen3:
        if mic_gain > 0:
            mic_gain -= 1
            call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)])

    if buttonTime2 >= 2 and not LEDOn and OLED_screen5:
        if not unmount_ok:
            unmount_cmd = "sudo umount /media/usb"
            os.system(unmount_cmd)
            unmount_ok = True

GPIO.add_event_detect(recordBTN, GPIO.BOTH, callback=my_callback, bouncetime=500)
GPIO.add_event_detect(displayBTN, GPIO.BOTH, callback=my_callback2, bouncetime=500)
GPIO.add_event_detect(usbBTN, GPIO.BOTH, callback=my_callback3, bouncetime=500)

# Scott's code
connected = False
ipaddr = '192.168.50.1' # static ip address of device
port = 8888
client_sock = None
server_sock = None
client_info = None
delay = 0
recording = False
# Thread that listens for connections on its ippadr and port, if it finds a connection it starts a recieve thread
def connect_thread():
    global client_sock, server_sock, client_info, connected
    connected = True
    client_sock, server_sock, client_info = phone_comm.open_server_socket(ipaddr,port)
    # Start recieve thread
    recv_thread = threading.Thread(target=recieve_cmd, args=(client_sock,))
    recv_thread.start()

# listen for user commands
def recieve_cmd(sock): 
    print("Recieve thread Started")
    while connected : 
        try:
            data = sock.recv(1024) 
            if data == b'':
                continue
            process_cmd(data)
        except:
            if not connected:
                break            
    print("Recieve thread Exiting")
    return

# process user commands        
def process_cmd(data):
    global recording
    if data == b'STARTRECORD':
        #start Recording
        recording = True
        my_callback(recordBTN) # This toggles recording
        #start streaming
        threading.Thread(target=stream_file_thread,args=() ).start()

    elif data == b'STOPRECORD':
        #stop recording
        recording = False
        my_callback(recordBTN) # This toggles recording
    return

# Thread that streams the files under current recording directory
def stream_file_thread():
    print("start file streaming thread")
    file_to_stream = save # location recordings are being saved
    file_count = 1
    while(recording):
        print("streaming file: ",file_to_stream)
        stream_file(file_to_stream) # this method blocks until the entire file is streamed
        file_count += 1
        file_to_stream = directory + "15-min-block-{:02d}.wav".format(file_count) # after the current file is finished, move onto the next
    return

# Streams the given file over the socket connection
def stream_file(file_name):
    global delay
    sampleRate = 44100
    bufferLengthSeconds = 0.1 # length of segments to send over the connection 
    bufferSize = (int) (sampleRate*4*bufferLengthSeconds) #convert seconds into # of bytes
    while not os.path.isfile(file_name):
        pass # wait until the file is started
    with open(file_name, 'rb') as file:
        start = time.time()
        # set up header
        header = bytearray(file.read(44))
        print('got header, should be b\'RIFF\': ',header[0:4])
        # input the buffersize into the header, so app knows how much to read
        struct.pack_into('<i',header,40, bufferSize)
        #start reading and sending files
        data = blocking_read(file, bufferSize)
        while len(data) > 0 and recording:
            client_sock.send(header)
            send_data(data,1024)
            
            elapsed = time.time()-start
            timestamp = file.tell()/4/sampleRate
            delay = (elapsed-timestamp)*1000
            
            print('Delay: {:.0f}ms'.format(delay), end = "\t")
            data = blocking_read(file, bufferSize)
            print('Time Elapsed: {:.3f}s'.format(elapsed))
        file.close()
    return

# Read data from the file until 'size' bytes have been read
def blocking_read(file, size):
    data = bytearray()
    while len(data) < size:
        data += bytearray(file.read(size - len(data)))
    return data
        
# send byte array 'a' in packets that are 'size' large         
def send_data(a, size):
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


# End Scott's code

# main loop
while True:
   usb_stats = subprocess.getoutput("ls -l /dev/disk/by-uuid/")

   # Draw a black filled box to clear the image.
   draw.rectangle((0, 0, width, height), outline=0, fill=0)

   hours, rem =divmod(time.time() - t, 3600)
   minutes, seconds = divmod(rem, 60)
   mic_gain_disp = round(mic_gain*6.67)

   dur = "  Duration: {:0>2}:{:0>2}:{:0>2}".format(int(hours), int(minutes), round(seconds))
   direc = "  Recording Number {}".format(buttonPress)

   #if 'C6FA-6FD7' in usb_stats: #USB ID for Test Unit 1. When changing this USB ID remember to also change the ID in "sudo nano /etc/fstab"
   if 'C6FA-6FD7' in usb_stats:  #USD ID for Final Unit 1. when changing this USB ID remember to also change the ID in "sudo nano /etc/fstab"
       if not os.path.ismount('/media/usb'):
            mount_cmd = "sudo mount -a"
            os.system(mount_cmd)
       usb_conn = True
       if unplug:
           unplug = False
           unmount_ok = False
   else:
       usb_conn = False
       unplug = True

   if usb_conn:
        if not unmount_ok:
            GPIO.output(readyLED, GPIO.HIGH)
            GPIO.output(audioSupplyVolt, GPIO.HIGH)
        else:
            GPIO.output(readyLED, GPIO.LOW)
            GPIO.output(audioSupplyVolt, GPIO.LOW)
   if not usb_conn:
            GPIO.output(readyLED, GPIO.LOW)
            GPIO.output(audioSupplyVolt, GPIO.LOW)
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.text((x, top+0), "    ***ERROR!***", font=font, fill=255)
            draw.text((x, top+16), " USB Drive NOT found", font=font, fill=255)
            draw.text((x, top+24), "  Please insert USB", font=font, fill=255)

   if OLED_main:
       if OLED_Rec:
           draw.text((x, top+0), "  Recording Audio...", font=font, fill=255)
           draw.text((x, top+15), direc, font=font, fill=255)
           draw.text((x, top+24), dur, font=font, fill=255)

       else:
           if usb_conn:
              draw.text((x, top+0), "  Recording Stopped", font=font, fill=255)

              if not unmount_ok:
                  draw.text((x, top+16), "    USB Mounted OK", font=font, fill=255)
                  draw.text((x, top+24), "  **Do NOT Remove!**", font=font, fill=255)
              else:
                  draw.text((x, top+16), "    USB Un-Mounted", font=font, fill=255)
                  draw.text((x, top+24), " **OK to remove USB**", font=font, fill=255)

           #if not usb_conn:


   if OLED_screen3 and usb_conn:
       draw.text((x, top+0), "Mic. Gain Control", font=font, fill=255)
       draw.text((x, top+16), str(mic_gain_disp), font=font, fill=255)

   if OLED_screen4 and usb_conn:
        # Scott's Code:
        draw.text((x, top+0), "Phone Setup", font=font, fill=255)
        # Create connection
        
        if not connected:
            draw.text((x, top+16), 'Listening on:',font=font, fill=255)
            draw.text((x, top+24), f'{ipaddr}:{port}',font=font, fill=255)
            threading.Thread(target=connect_thread, args=()).start()
        elif client_info:
            draw.text((x, top+16), 'Connected to:',font=font, fill=255)
            draw.text((x, top+24), f'{client_info[0]}:{client_info[1]}',font=font, fill=255)
            draw.text((x, top+32), f'{time.time()}',font=font, fill=255)
            if delay>0:
                draw.text((x, top+32), "delay: {:.0f}ms".format(delay), font=font, fill=255)
        else:
            draw.text((x, top+16), 'Listening on:',font=font, fill=255)
            draw.text((x, top+24), f'{ipaddr}:{port}',font=font, fill=255)
       # End Scott's Code

   if OLED_screen5 and usb_conn:
       # Scott's code
       if connected:
           connected = False # no phone connection anymore
           phone_comm.stop()
           if(server_sock):
               print("closing server socket")
               server_sock.close()
               server_sock = None
           if(client_sock):
               client_sock.close()
               client_sock = None
               client_info = None
               
       # End Scott's code
       draw.text((x, top+0), "USB Unmount", font=font, fill=255)

   if OLED_screen2 and usb_conn:
       cmd = "free -m | awk 'NR==2{printf \"Mem: %d/%d MB   %d%%\", $3,$2,$3*100/$2}'"
       MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
       cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%d GB     %s\", $3,$2,$5}'"
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
   disp.display()

   time.sleep(1)