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

class AnalogPin(object):
    def __init__(self, adc, adc_pin):
        self.adc = adc
        self.adc_pin = adc_pin
        self.last_raw_reading = None
        self.last_reading = None

    def read_raw(self, gain=1):
        raw_reading = adc.read_adc(self.adc_pin, gain=gain)
        self.last_raw_reading = raw_reading
        return raw_reading

    def read(self, gain=1):
        raw_reading = self.read_raw(gain=gain)
        reading = 4.096 * float(raw_reading) / 32767
        self.last_reading = reading
        return reading

class Thermistor(object):
    def __init__(self, reference_pin, thermistor_pin):
        self.reference_pin = reference_pin
        self.thermistor_pin = thermistor_pin
        self.reading = None
        self.referenced_reading = None

    def read(self, gain=1):
        v_ref = self.reference_pin.read(gain)
        v_reading = self.thermistor_pin.read(gain)
        self.reading = v_reading
        self.referenced_reading = v_ref - v_reading
        return (self.reading, self.referenced_reading)
