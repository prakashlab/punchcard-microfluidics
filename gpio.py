import datetime
import time

import numpy as np

import RPi.GPIO as GPIO

def cleanup():
    GPIO.cleanup()


# State

class BinaryState(object):
    def __init__(self):
        self.state = None
        self.after_state_change = None

    def set_state(self, state):
        self.state = state
        if callable(self.after_state_change):
            self.after_state_change(self.state)

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
            self.adc_pin_differential = analog_pin_differentials[(adc_pin, ref_pin)]
        except KeyError:
            raise ValueError(
                'Cannot define a differential analog pin reading pin {} '
                'and referencing pin {}!'.format(adc_pin, ref_pin)
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

class Thermistor(object):
    def __init__(
        self, reference_pin, thermistor_pin, bias_resistance=1962,
        A=1.125308852122e-03, B=2.34711863267e-04, C=8.5663516e-08
    ):
        self.reference_pin = reference_pin
        self.thermistor_pin = thermistor_pin
        self.reading = None
        self.referenced_reading = None
        self.bias_resistance = bias_resistance
        self.A = A
        self.B = B
        self.C = C

    def calibrate_steinhart_hart(self, temperature_resistance_pairs, unit='C'):
        (temperatures, resistances) = zip(*temperature_resistance_pairs)

        T = np.array(temperatures)
        if unit == 'K':
            pass
        elif unit == 'C':
            T = T + 273.15
        else:
            raise ValueError('Unknown temperature unit: {}'.format(unit))
        b = 1 / T

        R = np.expand_dims(np.array(resistances), axis=1)
        A = np.hstack((np.ones_like(R), np.log(R), np.power(np.log(R), 3)))
        (coeffs, residuals, rank, singular_values) = np.linalg.lstsq(A, b)
        (self.A, self.B, self.C) = coeffs
        return (coeffs, residuals)

    def read_voltage(self):
        ref = self.reference_pin.read_raw()
        reading = self.thermistor_pin.read_raw()
        self.reading = reading
        self.referenced_reading = ref - reading
        return (self.reading, self.referenced_reading)

    def read_resistance(self):
        (reading, referenced_reading) = self.read_voltage()
        if referenced_reading <= 0:
            return None

        return reading * self.bias_resistance / referenced_reading

    def read(self, unit='C'):
        R = self.read_resistance()
        if R is None:
            return None

        T_Kelvin = 1 / (self.A + self.B * np.log(R) + self.C * np.power(np.log(R), 3))
        if unit == 'K':
            return T_Kelvin
        elif unit == 'C':
            T_Celsius = T_Kelvin - 273.15
            return T_Celsius
        else:
            raise ValueError('Unknown temperature unit: {}'.format(unit))
