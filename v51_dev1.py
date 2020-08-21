#!/usr/bin/env python3.5.3

import RPi.GPIO as GPIO
import time
import subprocess
from subprocess import call
import os
import io
import signal
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306

firmware = os.path.basename(__file__)

def getserial():
    #extract serial number from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

myserial = getserial()

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
image = Image.open('/home/pi/Documents/Python/splash1.png').convert('1')

# Display image.
disp.image(image)
disp.display()
time.sleep(2.5)

# Clear display.
disp.clear()
disp.display()

# Display Splash Screen 2
image = Image.open('/home/pi/Documents/Python/splash2.png').convert('1')

# Display image.
disp.image(image)
disp.display()
time.sleep(2.5)

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

draw.rectangle((0, 0, width, height), outline=0, fill=0)
draw.rectangle((0, 0, width, 9), outline=0, fill=255)
draw.text((x, top+1), "      ASAD-III    ", font=font, fill=0)
draw.text((x, top+16), "F/W: {}".format(firmware), font=font, fill=255)
draw.text((x, top+24), "S/N: {}".format(myserial), font=font, fill=255)
disp.image(image)
disp.display()
time.sleep(5)

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
OLED_screen6 = False
loop_back = False
loop_back_rev = False
usb_conn = False
unmount_ok = False
unplug = False
lights_on = True
buttonPress = 0
t = 0
mic_gain = 9
call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)], stdout=open(os.devnull, 'wb'))

def my_callback(channel):
    global buttonPress, LEDOn, OLED_Rec, rec, rec_vars, directory, name, save, t, lights_on

    if not unmount_ok and not unplug:
        if LEDOn:
            LEDOn = False
            OLED_Rec = False
            os.killpg(rec.pid, signal.SIGTERM)
            rec.terminate()
            rec = None
        else:
            LEDOn = True
            OLED_Rec = True
            t = time.time()
            buttonPress += 1
            directory = '/media/usb/Recording Number {}/'.format(buttonPress)

            if not os.path.exists(directory):
                os.mkdir(directory)

            name = '15-min-block.wav'
            save = directory + name
            rec_vars = ['arecord', '-f', 'cd', '--max-file-time', '900', save]
            rec = subprocess.Popen(rec_vars, shell=False, preexec_fn=os.setsid)


def my_callback2(channel):
    global displayBTN_press, usb_conn, OLED_main, OLED_screen2, OLED_screen3, OLED_screen4, OLED_screen5, OLED_screen6, loop_back, mic_gain, lights_on

    start_timer1 = time.time()

    while GPIO.input(channel) == 0: #wait for button press
        pass

    buttonTime1 = time.time() - start_timer1

    if .1 <= buttonTime1 < 1 and usb_conn:
        if OLED_screen6:
            OLED_screen6 = False
            loop_back = True

        if OLED_screen5:
            OLED_screen5 = False
            OLED_screen6 = True

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

    if buttonTime1 >= 1 and OLED_screen2:
        if mic_gain < 15:
            mic_gain += 1
            call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)], stdout=open(os.devnull, 'wb'))

    if buttonTime1 >= 1 and OLED_screen4:
        if not lights_on:
            lights_on = True

def my_callback3(channel):
    global usbBTN_press, LEDOn, unmount_ok, OLED_main, OLED_screen2, OLED_screen3, OLED_screen4, OLED_screen5, OLED_screen6, loop_back_rev, mic_gain, lights_on

    start_timer2 = time.time()

    while GPIO.input(channel) == 0: #wait for button press
        pass

    buttonTime2 = time.time() - start_timer2

    if .1 <= buttonTime2 < 1 and usb_conn:
        if OLED_main:
            OLED_main = False
            loop_back_rev = True

        if OLED_screen2:
            OLED_screen2 = False
            OLED_main = True

        if OLED_screen3:
            OLED_screen3 = False
            OLED_screen2 = True

        if OLED_screen4:
            OLED_screen4 = False
            OLED_screen3 = True

        if OLED_screen5:
            OLED_screen5 = False
            OLED_screen4 = True

        if OLED_screen6:
            OLED_screen6 = False
            OLED_screen5 = True
            loop_back_rev = False

        if loop_back_rev:
            OLED_screen6 = True

    if buttonTime2 >= 1 and OLED_screen2:
        if mic_gain > 0:
            mic_gain -= 1
            call(['/usr/bin/amixer', 'set', 'Capture', '{}'.format(mic_gain)], stdout=open(os.devnull, 'wb'))

    if buttonTime2 >= 1 and not LEDOn and OLED_screen3:
        if not unmount_ok:
            unmount_cmd = "sudo umount /media/usb"
            os.system(unmount_cmd)
            unmount_ok = True

    if buttonTime2 >= 1 and OLED_screen4:
        if lights_on:
            lights_on = False

GPIO.add_event_detect(recordBTN, GPIO.BOTH, callback=my_callback, bouncetime=500)
GPIO.add_event_detect(displayBTN, GPIO.BOTH, callback=my_callback2, bouncetime=500)
GPIO.add_event_detect(usbBTN, GPIO.BOTH, callback=my_callback3, bouncetime=500)

# main loop
while True:
   usb_stats = subprocess.getoutput("ls -l /dev/disk/by-uuid/")

   # Draw a black filled box to clear the image.
   draw.rectangle((0, 0, width, height), outline=0, fill=0)
   draw.rectangle((0, 0, width, 9), outline=0, fill=255)

   hours, rem =divmod(time.time() - t, 3600)
   minutes, seconds = divmod(rem, 60)
   mic_gain_disp = round(mic_gain*6.67)

   dur = " Duration: {:0>2}:{:0>2}:{:0>2}".format(int(hours), int(minutes), round(seconds))
   direc = " Recording Number {}".format(buttonPress)

   #if 'C6FA-6FD7' in usb_stats: #USB ID for Test Unit 1. When changing this USB ID remember to also change the ID in "sudo nano /etc/fstab"
   if 'DF4C-7681' in usb_stats:  #USD ID for Final Unit 1. when changing this USB ID remember to also change the ID in "sudo nano /etc/fstab"
       usb_conn = True
       if unplug:
           unplug = False
           unmount_ok = False
   else:
       usb_conn = False
       unplug = True

   if usb_conn:
        if not unmount_ok:
            if lights_on:
                GPIO.output(readyLED, GPIO.HIGH)
            elif not lights_on:
                GPIO.output(readyLED, GPIO.LOW)
            GPIO.output(audioSupplyVolt, GPIO.HIGH)
        else:
            GPIO.output(readyLED, GPIO.LOW)
            GPIO.output(audioSupplyVolt, GPIO.LOW)
   if not usb_conn:
            GPIO.output(readyLED, GPIO.LOW)
            GPIO.output(audioSupplyVolt, GPIO.LOW)
            draw.text((x, top+1), "     ***ERROR!***", font=font, fill=0)
            draw.text((x, top+12), " USB Drive NOT found", font=font, fill=255)
            draw.text((x, top+24), "  Please insert USB", font=font, fill=255)

   if OLED_main:
       if OLED_Rec:
           draw.text((x, top+1), "  RECORDING AUDIO...", font=font, fill=0)
           draw.text((x, top+12), direc, font=font, fill=255)
           draw.text((x, top+24), dur, font=font, fill=255)

       else:
           if usb_conn:
              draw.text((x, top+1), "  RECORDING STOPPED", font=font, fill=0)

              if not unmount_ok:
                  draw.text((x, top+12), "Device ready...", font=font, fill=255)
                  draw.text((x, top+24), "PRESS START       -->", font=font, fill=255)
              else:
                  draw.text((x, top+16), "  Device NOT ready!", font=font, fill=255)
                  draw.text((x, top+24), "** USB UNMOUNTED **", font=font, fill=255)


   if OLED_screen2 and usb_conn:
       draw.rectangle((0, 16, 30, 30), outline=0, fill=255)
       draw.text((x, top+1), "   MIC GAIN CONTROL", font=font, fill=0)
       draw.text((x+2, top+20), "{}%".format(mic_gain_disp), font=font, fill=0)
       draw.text((x, top+16), "      Black  = +  -->", font=font, fill=255)
       draw.text((x, top+24), "      Yellow = -  -->", font=font, fill=255)

   if OLED_screen5 and usb_conn:
       draw.text((x, top+1), "     PHONE SETUP", font=font, fill=0)

   if OLED_screen3 and usb_conn:
       if not unmount_ok:
            draw.text((x, top+1), "    USB IS MOUNTED", font=font, fill=0)
            draw.text((x, top+16), "Hold yellow button", font=font, fill=255)
            draw.text((x, top+24), "to un-mount      -->", font=font, fill=255)
       else:
           draw.text((x, top+1), "   USB IS UNMOUNTED", font=font, fill=0)
           draw.text((x, top+16), "   OK to remove USB", font=font, fill=255)
           draw.text((x, top+24), "     from device", font=font, fill=255)

   if OLED_screen4 and usb_conn:
       if lights_on:
           draw.text((x, top+1), "      LIGHTS ON", font=font, fill=0)
           draw.text((x, top+16), "Hold yellow button", font=font, fill=255)
           draw.text((x, top+24), "to turn off LEDS  -->", font=font, fill=255)
           os.system("echo mmc0 > /sys/class/leds/led0/trigger")
       else:
           draw.text((x, top+1), "      LIGHTS OFF", font=font, fill=0)
           draw.text((x, top+16), "Hold black button-->", font=font, fill=255)
           draw.text((x, top+24), "to turn on LEDS", font=font, fill=255)
           os.system("echo none > /sys/class/leds/led0/trigger")

   if OLED_screen6 and usb_conn:
       cmd = "free -m | awk 'NR==2{printf \"Mem: %d/%d MB   %d%%\", $3,$2,$3*100/$2}'"
       MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
       cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%d GB     %s\", $3,$2,$5}'"
       Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")

       temp_read = open("/sys/class/thermal/thermal_zone0/temp", "r")
       temp_raw = float(temp_read.readline ())
       temperature = temp_raw/1000

       temp_message = "Temperature:   {:.1f}'C".format(temperature)

       draw.text((x, top+1), "     DEVICE STATS", font=font, fill=0)
       draw.text((x, top+9), MemUsage, font=font, fill=255)
       draw.text((x, top+17), Disk, font=font, fill=255)
       draw.text((x, top+25), temp_message, font=font, fill=255)

   if not unmount_ok and not unplug:
        if OLED_Rec:
            if lights_on:
                GPIO.output(recordLED, GPIO.HIGH)
            elif not lights_on:
                GPIO.output(recordLED, GPIO.LOW)

        else:
            GPIO.output(recordLED, GPIO.LOW)


   # Display image.
   disp.image(image)
   disp.display()

   time.sleep(1)