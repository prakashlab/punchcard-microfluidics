import RPi.GPIO as GPIO
import Adafruit_ADS1x15


def cleanup():
    GPIO.cleanup()


# State

class State(object):
    def __init__(self, initial_state=None):
        self.state = initial_state
        self.after_state_change = None

    def set_state(self, state):
        self.state = state
        if callable(self.after_state_change):
            self.after_state_change(self.state)


class BinaryState(State):
    def turn_on(self):
        self.set_state(True)

    def turn_off(self):
        self.set_state(False)

    def toggle(self):
        prev_state = self.state
        if prev_state:
            self.turn_off()
        else:
            self.turn_on()
        return self.state


# Digital IO

class DigitalPin(BinaryState):
    def __init__(self, pin, initial_state=False):
        super().__init__()
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)
        self.set_state(initial_state)

    def set_state(self, state):
        GPIO.output(self.pin, state)
        super().set_state(state)


# Analog IO

analog_pin_differentials = {
    (0, 1): 0,
    (0, 3): 1,
    (1, 3): 2,
    (2, 3): 3
}

gain_voltage_maxes = {
    1: 4.096,
    2: 2.048,
    4: 1.024,
    8: 0.512,
    16: 0.256
}

ADC = Adafruit_ADS1x15.ADS1115


class PWMPin(State):
    def __init__(self, pin=18, frequency=1000, initial_state=0):
        super().__init__(initial_state=initial_state)
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        self.frequency = frequency
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, frequency)
        self.pwm.start(self.state)

    def set_frequency(self, frequency):
        self.pwm.ChangeFrequency(frequency)

    def set_state(self, state):
        self.pwm.ChangeDutyCycle(100.0 * state)
        super().set_state(state)

    def turn_off(self):
        self.set_state(0)


class AnalogPin(object):
    def __init__(self, adc, adc_pin, gain=1, adc_max=32767):
        self.adc = adc
        self.adc_pin = adc_pin
        self.adc_max = float(adc_max)
        self.gain = gain
        try:
            self.voltage_max = gain_voltage_maxes[gain]
        except KeyError:
            raise ValueError('Unsupported ADC gain: {}'.format(gain))
        self.last_raw_reading = None
        self.last_reading = None

    def read_raw(self):
        raw_reading = self.adc.read_adc(self.adc_pin, gain=self.gain)
        self.last_raw_reading = raw_reading
        return raw_reading

    def read(self):
        raw_reading = self.read_raw()
        reading = self.voltage_max * float(raw_reading) / self.adc_max
        self.last_reading = reading
        return reading


class DifferentialAnalogPin(AnalogPin):
    def __init__(self, *args, ref_pin, **kwargs):
        super().__init__(*args, **kwargs)
        self.ref_pin = ref_pin
        try:
            self.adc_pin_differential = analog_pin_differentials[(
                self.adc_pin, self.ref_pin
            )]
        except KeyError:
            raise ValueError(
                'Cannot define a differential analog pin reading pin {} '
                'and referencing pin {}!'.format(self.adc_pin, self.ref_pin)
            )

    def read_raw(self):
        raw_reading = self.adc.read_adc_difference(
            self.adc_pin_differential, gain=self.gain
        )
        self.last_raw_reading = raw_reading
        return raw_reading


# Components

class HBridgeDevice(object):
    def __init__(self, pin_1, pin_2):
        self.digital_pin_1 = DigitalPin(pin_1)
        self.digital_pin_2 = DigitalPin(pin_2)

    def turn_on_forwards(self):
        self.digital_pin_2.turn_off()
        self.digital_pin_1.turn_on()

    def turn_on_backwards(self):
        self.digital_pin_1.turn_off()
        self.digital_pin_2.turn_on()

    def turn_off(self):
        self.digital_pin_1.turn_off()
        self.digital_pin_2.turn_off()
