import datetime
import time

import RPi.GPIO as GPIO

def cleanup():
    GPIO.cleanup()

class DigitalPin(object):
    def __init__(self, pin):
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)
        self.state = None
        self.set_state(False)

    def set_state(self, state):
        GPIO.output(self.pin, state)
        self.state = state

    def turn_on(self):
        self.set_state(True)

    def turn_off(self):
        self.set_state(False)
