import numpy as np


# Components

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

        T_Kelvin = float(
            1 / (self.A + self.B * np.log(R) + self.C * np.power(np.log(R), 3))
        )
        if unit == 'K':
            return T_Kelvin
        elif unit == 'C':
            T_Celsius = T_Kelvin - 273.15
            return T_Celsius
        else:
            raise ValueError('Unknown temperature unit: {}'.format(unit))


# Control

class Control(object):
    def __init__(self, initial_setpoint=None, setpoint_reached_epsilon=0):
        self.setpoint = initial_setpoint
        self.after_setpoint_change = None
        self.setpoint_reached = False
        self.setpoint_reached_epsilon = setpoint_reached_epsilon

    def reset_setpoint_reached(self):
        self.setpoint_reached = False

    def set_setpoint(self, setpoint):
        if setpoint == self.setpoint:
            return

        self.setpoint = setpoint
        self.reset_setpoint_reached()
        if callable(self.after_setpoint_change):
            self.after_setpoint_change(self.setpoint)

    def compute_error(self, measurement):
        if self.setpoint is None or measurement is None:
            return None

        return measurement - self.setpoint

    def compute_setpoint_reached(self, measurement):
        error = self.compute_error(measurement)
        if error is None:
            return None

        return (
            abs(self.compute_error(measurement))
            < self.setpoint_reached_epsilon
        )

    def compute_control_effort(self, measurement):
        return None

    def update(self, measurement):
        if self.compute_setpoint_reached(measurement):
            self.setpoint_reached = True


class InfiniteGainControl(Control):
    """Toggle control effort by comparing measurement with setpoint.

    Equivalent to proportional control with infinite gain.

    Direction specifies whether control effort tends to increase or decrease
    the controlled value.
    """
    def __init__(self, direction=True, *args, **kwargs):
        self.direction = direction
        super().__init__(*args, **kwargs)

    def compute_control_effort(self, measurement):
        if self.setpoint is None:
            return False
        if measurement is None:
            return None

        error = self.compute_error(measurement)
        if self.direction:
            return error < 0
        else:
            return error > 0


class HeaterController(object):
    def __init__(self, control, heater, thermistor):
        self.control = control
        self.heater = heater
        self.thermistor = thermistor
        self.last_temperature = None

    def update(self):
        temperature = self.thermistor.read()
        if temperature is None:
            return (None, None)

        self.last_temperature = temperature
        self.control.update(temperature)
        control_effort = self.control.compute_control_effort(
            temperature
        )
        if self.control.setpoint is not None:
            self.heater.set_state(control_effort)

        return (temperature, control_effort)
