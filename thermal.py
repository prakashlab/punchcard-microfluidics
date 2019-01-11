import sys
import time
from datetime import datetime

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


# Feedback Control

class Control(object):
    """Generic feedback control interface. Implement compute_control_effort.

    Direction specifies whether control effort tends to increase or decrease
    the controlled value.
    """
    def __init__(
        self, initial_setpoint=None, setpoint_reached_epsilon=0, direction=True
    ):
        self.setpoint = initial_setpoint
        self.after_setpoint_change = None
        self.setpoint_reached = False
        self.setpoint_reached_epsilon = setpoint_reached_epsilon
        self.direction = direction

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

        return self.setpoint - measurement

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
        if self.setpoint is None:
            self.setpoint_reached = None
        else:
            setpoint_reached = self.compute_setpoint_reached(measurement)
            if setpoint_reached:
                self.setpoint_reached = True


class InfiniteGainControl(Control):
    """Toggle control effort by comparing measurement with setpoint.

    Equivalent to proportional control with infinite gain.
    """
    def compute_control_effort(self, measurement):
        if self.setpoint is None:
            return False
        if measurement is None:
            return None

        error = self.compute_error(measurement)
        if self.direction:
            return error > 0
        else:
            return error < 0


class ProportionalControl(Control):
    """Scale control effort linearly with error."""
    def __init__(self, gain, *args, **kwargs):
        self.gain = gain
        super().__init__(*args, **kwargs)

    def compute_control_effort(self, measurement):
        if self.setpoint is None:
            return 0
        if measurement is None:
            return None

        error = self.compute_error(measurement)
        gain = self.gain if self.direction else -self.gain
        return max(0.0, min(1.0, gain * error))


# Lysis Heater Thermal Module

class ThermalControllerReporter(object):
    def __init__(
        self, interval=0.5, control_efforts=('Thermal Control Effort',),
        file_prefix='', file_suffix=''
    ):
        self.interval = interval
        self.start_time = None
        self.next_report_index = None
        self.enabled = False
        self.control_efforts = control_efforts
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
        self.file = None

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def reset(self):
        self.start_time = None
        self.next_report_index = None
        self.close_report()
        self.enable()

    def close_report(self):
        if self.file is not None:
            self.file.close()
            self.file = None

    def update(
        self, temperature, setpoint=None, setpoint_reached=None,
        control_efforts=[]
    ):
        if not self.enabled or temperature is None:
            return

        current_time = time.time()
        if self.next_report_index is None:  # First report received!
            self.start_time = current_time
            self.next_report_index = 0
            self.open_report()
            self.report_header()
        next_report_time = (
            self.next_report_index * self.interval + self.start_time
        )
        if current_time >= next_report_time:
            self.report(
                current_time, temperature,
                setpoint=setpoint, setpoint_reached=setpoint_reached,
                control_efforts=control_efforts
            )
            self.next_report_index += 1

    def open_report(self):
        filename = self.generate_filename()
        print('Logging to {}...'.format(filename))
        self.file = open(filename, 'w')

    def report_header(self):
        header_string = (
            'Time (s),'
            'Temperature (deg C),Setpoint (deg C),Error (deg C),'
            '{}Setpoint Reached'
        ).format(
            '{},'.format(','.join(self.control_efforts))
            if self.control_efforts else ''
        )
        print(header_string, file=self.file)
        self.file.flush()

    def generate_timestamp(self, time):
        return datetime.fromtimestamp(time).isoformat(sep='_')

    def generate_filename(self):
        return '{}{}{}.csv'.format(
            self.file_prefix,
            self.generate_timestamp(self.start_time),
            self.file_suffix
        )

    def report(
        self, report_time, temperature, setpoint=None, setpoint_reached=None,
        control_efforts=[]
    ):
        error = None
        if setpoint is not None:
            error = setpoint - temperature

        control_efforts_string = self.format_control_efforts(control_efforts)
        report_string = '{:.2f},{:.1f},{},{},{}{}'.format(
            report_time - self.start_time,
            temperature,
            '{:.1f}'.format(setpoint) if setpoint is not None else '',
            '{:.1f}'.format(error) if error is not None else '',
            '{},'.format(control_efforts_string)
            if control_efforts_string else '',
            setpoint_reached if setpoint_reached is not None else ''
        )

        print(report_string, file=self.file)
        self.file.flush()

    def format_control_efforts(self, control_efforts):
        formatted_control_efforts = [
            '{:.2f}'.format(float(effort)) if effort is not None else ''
            for effort in control_efforts
        ]
        return ','.join(formatted_control_efforts)


class ThermalControllerPrinter(ThermalControllerReporter):
    def __init__(
        self, interval=15, control_efforts=('Thermal Control Effort',),
    ):
        super().__init__(interval=interval, control_efforts=control_efforts)

    def close_report(self):
        pass

    def open_report(self):
        self.file = sys.stdout


class HeaterController(object):
    def __init__(
        self, control, heater, thermistor,
        file_reporter=None, print_reporter=None
    ):
        self.control = control
        self.heater = heater
        self.thermistor = thermistor

        self.last_temperature = None
        self.last_control_effort = None

        self.file_reporter = file_reporter
        self.print_reporter = print_reporter
        self.reporters = [self.file_reporter, self.print_reporter]
        for reporter in self.reporters:
            if reporter is not None:
                reporter.control_efforts = ('Heater PWM Duty',)

    def reset(self):
        for reporter in self.reporters:
            if reporter is not None:
                reporter.reset()
        self.control.reset_setpoint_reached()
        self.last_control_effort = 0

    def update(self):
        temperature = self.thermistor.read()
        if temperature is None:
            return (None, None)

        self.last_temperature = temperature
        self.control.update(temperature)
        control_effort = self.control.compute_control_effort(temperature)
        self.last_control_effort = control_effort
        self.heater.set_state(control_effort)

        for reporter in self.reporters:
            if reporter is not None:
                reporter.update(
                    temperature, setpoint=self.control.setpoint,
                    setpoint_reached=self.control.setpoint_reached,
                    control_efforts=(control_effort,)
                )

        return (temperature, (control_effort,))
