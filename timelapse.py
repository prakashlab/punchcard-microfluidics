iso = 60
shutter_speed = 200000
interval = 1
prefix = ''
duration =30;

prefix = prefix + '_interval = ' + str(interval) + ' s_'

import tkinter as tk
import datetime
from picamera import PiCamera
from scipy import misc

### LED, stepper control ###
import RPi.GPIO as GPIO
from time import sleep
import time

# pin def
ledPIN = 19
laserPIN = 26
x_stepPin = 23
x_dirPin = 24
x_enablePin = 27
y_stepPin = 14
y_dirPin = 15
y_enablePin = 3

z_stepPin = 16
z_dirPin = 20

def initDriver():
	GPIO.setmode(GPIO.BCM)  # set board mode to Broadcom
	
	GPIO.setup(ledPIN, GPIO.OUT)
	GPIO.setup(laserPIN, GPIO.OUT)
	
	GPIO.setup(x_stepPin, GPIO.OUT)
	GPIO.setup(x_dirPin, GPIO.OUT)
	GPIO.setup(x_enablePin, GPIO.OUT)
	GPIO.setup(y_stepPin, GPIO.OUT)
	GPIO.setup(y_dirPin, GPIO.OUT)
	GPIO.setup(y_enablePin, GPIO.OUT)
	GPIO.setup(z_stepPin, GPIO.OUT)
	GPIO.setup(z_dirPin, GPIO.OUT)

	
	
def ledON():
	GPIO.output(ledPIN,1)

def ledOFF():
	GPIO.output(ledPIN,0)

def laserON():
	GPIO.output(laserPIN,1)

def laserOFF():
	GPIO.output(laserPIN,0)

def x_move(direction,steps,dt):
    if 'f' == direction:
        GPIO.output(x_dirPin, 0)
    else:
        GPIO.output(x_dirPin, 1)
    GPIO.output(x_enablePin, 0)
    for i in range(steps):
        GPIO.output(x_stepPin,0)
        sleep(dt/2)
        GPIO.output(x_stepPin,1)
        sleep(dt/2)
    GPIO.output(x_enablePin, 1)
		
def y_move(direction,steps,dt):
    if 'f' == direction:
        GPIO.output(y_dirPin, 0)
    else:
        GPIO.output(y_dirPin, 1)
    GPIO.output(y_enablePin, 0)
    for i in range(steps):
        GPIO.output(y_stepPin,0)
        sleep(dt/2)
        GPIO.output(y_stepPin,1)
        sleep(dt/2)
    GPIO.output(y_enablePin, 1)
		
def z_move(direction,steps,dt):
    if 'f' == direction:
        GPIO.output(z_dirPin, 0)
    else:
        GPIO.output(z_dirPin, 1)
    for i in range(steps):
        GPIO.output(z_stepPin,0)
        sleep(dt/2)
        GPIO.output(z_stepPin,1)
        sleep(dt/2)

# init.
initDriver()
ledOFF();
laserOFF();

# set up camera
camera = PiCamera(resolution='3280x2464',sensor_mode=2,framerate=5)
camera.iso = iso
# camera.exposure_mode = 'off'
camera.shutter_speed = shutter_speed
camera.awb_mode = 'off'
camera.awb_gains = (2,1)
camera.start_preview(resolution=(1640, 1232),fullscreen=False, window=(800, 0, 820, 616))

sleep(2)
camera.iso = iso
camera.exposure_mode = 'off'
camera.shutter_speed = shutter_speed
camera.awb_mode = 'off'
camera.awb_gains = (2,1)

# shutter_speed = 2000
    
for i in range(int(duration/interval)):
    laserON()
    camera.shutter_speed = shutter_speed
    camera.capture(prefix + str(i).zfill(3) + '.jpeg')
    laserOFF()
    print(camera.analog_gain)
    print(camera.digital_gain)
    sleep(interval)

# exit routine
GPIO.cleanup()
