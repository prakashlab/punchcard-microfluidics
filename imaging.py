import datetime
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

class Camera(object):
    def __init__(
        self, pi_camera, iso=60, exposure_mode='off', shutter_speed=500,
        awb_mode='off', awb_gains=(2, 1)
    ):
        self.pi_camera = pi_camera
        pi_camera.iso = iso
        pi_camera.exposure_mode = exposure_mode
        pi_camera.shutter_speed = shutter_speed
        pi_camera.awb_mode = awb_mode
        pi_camera.awb_gains = awb_gains
        self.zoom = None

    def set_roi(self, zoom):
        self.zoom = zoom
        x_start = 0.5 - 1 / (2 * zoom)
        y_start = x_start
        width = 1 / zoom
        height = width
        self.pi_camera.zoom = (x_start, y_start, width, height)

    def set_shutter_speed(self, shutter_speed):
        speed_int = int(float(shutter_speed) * 1000)
        current_framerate = self.pi_camera.framerate
        new_framerate = int(1000000 / float(speed_int))
        self.pi_camera.framerate = min(new_framerate, 30)
        self.pi_camera.shutter_speed = speed_int

    def capture(
        self, filename_prefix, shutter_speed, zoom, resolution=(3280, 2464)
    ):
        timestamp = '{:%Y-%m-%d %H-%M-%S-%f}'.format(
            datetime.datetime.now()
        )[:-3]
        filename = '{}_{}x_{}us_{}.jpeg'.format(
            filename_prefix, int(zoom), shutter_speed, timestamp
        )
        print('Saving capture to:', filename)
        self.pi_camera.resolution = resolution
        self.pi_camera.capture(filename)
