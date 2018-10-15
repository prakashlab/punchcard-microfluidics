import time

from picamera import PiCamera
import RPi.GPIO as gpio

class DigitalPin(object):
    def __init__(self, pin):
        gpio.setmode(gpio.BCM)
        self.pin = pin
        gpio.setup(pin, gpio.OUT)
        self.state = None
        self.set_state(False)

    def set_state(self, state):
        gpio.output(self.pin, state)
        self.state = state

    def turn_on(self):
        self.set_state(True)

    def turn_off(self):
        self.set_state(False)

class StageAxis(object):
    FORWARDS = 'f'
    BACKWARDS = 'b'

    def __init__(self, step_pin, dir_pin, enable_pin=None):
        self.step_pin = DigitalPin(step_pin)
        self.dir_pin = DigitalPin(dir_pin)
        if enable_pin is not None:
            self.enable_pin = DigitalPin(enable_pin)
        else:
            self.enable_pin = None

    def move(self, direction, steps, dt):
        if direction == StageAxis.FORWARDS:
            self.dir_pin.turn_on()
        elif direction == StageAxis.BACKWARDS:
            self.dir_pin.turn_off()
        else:
            raise ValueError('Unknown StageAxis direction: {}'.format(direction))
        if self.enable_pin is not None:
            self.enable_pin.turn_off()
        for step in range(steps):
            self.step_pin.turn_off()
            time.sleep(dt / 2)
            self.step_pin.turn_on()
            time.sleep(dt / 2)
        if self.enable_pin is not None:
            self.enable_pin.turn_on()
