import datetime
import math
import time

import RPi.GPIO as GPIO

def cleanup():
    GPIO.cleanup()


# Digital IO

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


# Analog IO

analog_pin_differentials = {
    (0, 1): 0,
    (0, 3): 1,
    (1, 3): 2,
    (2, 3): 3
}

def analog_raw_to_volt(analog_raw):
    return 4.096 * float(analog_raw) / 32767


class AnalogPin(object):
    def __init__(self, adc, adc_pin):
        self.adc = adc
        self.adc_pin = adc_pin
        self.last_raw_reading = None
        self.last_reading = None

    def read_raw(self, gain=1):
        raw_reading = self.adc.read_adc(self.adc_pin, gain=gain)
        self.last_raw_reading = raw_reading
        return raw_reading

    def read(self, gain=1):
        raw_reading = self.read_raw(gain=gain)
        reading = analog_raw_to_volt(raw_reading)
        self.last_reading = reading
        return reading

class DifferentialAnalogPin(AnalogPin):
    def __init__(self, adc, adc_pin, ref_pin):
        super().__init__(adc, adc_pin)
        self.ref_pin = ref_pin
        try:
            self.adc_pin_differential = analog_pin_differentials[(adc_pin, ref_pin)]
        except KeyError:
            raise ValueError(
                'Cannot define a differential analog pin reading pin {} '
                'and referencing pin {}!'.format(adc_pin, ref_pin)
            )

    def read_raw(self, gain=1):
        raw_reading = self.adc.read_adc_difference(self.adc_pin_differential, gain=gain)
        self.last_raw_reading = raw_reading
        return raw_reading

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
    def __init__(self, reference_pin, thermistor_pin):
        self.reference_pin = reference_pin
        self.thermistor_pin = thermistor_pin
        self.reading = None
        self.referenced_reading = None
        self.A = 0.001125308852122
        self.B = 0.000234711863267
        self.C = 0.000000085663516

    def read_voltage(self, gain=1):
        v_ref = self.reference_pin.read(gain)
        v_reading = self.thermistor_pin.read(gain)
        self.reading = v_reading
        self.referenced_reading = v_ref - v_reading
        return (self.reading, self.referenced_reading)

    def read(self, unit='C'):
        (voltage, referenced_voltage) = self.read_voltage()
        if referenced_voltage <= 0:
            return None

        R = voltage * 1962 / referenced_voltage # in the other code, it was 1966 instead of 1962
        T_Kelvin = 1 / (self.A + self.B * math.log(R) + self.C * math.pow(math.log(R), 3))
        # T_Kelvin = 1 / (1 / 298.15 + (1 / 3950) * np.log(R_thermistor / 10000))
        if unit == 'K':
            return T_Kelvin
        elif unit == 'C':
            T_Celsius = T_Kelvin - 273.15
            return T_Celsius
        else:
            raise ValueError('Unknown temperature unit: {}'.format(unit))
