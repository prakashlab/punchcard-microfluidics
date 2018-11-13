import readline

import Adafruit_ADS1x15

import gpio

def read_float(prompt):
    while True:
        value = input(prompt).strip()
        if value == '':
            return None
        try:
            return float(value)
        except ValueError:
            print('Error: could not parse input as float: {}'.format(value))

def read_bias_resistance():
    return read_float('Please enter the resistance of the bias resistor in Ohms: ')

def read_temperature():
    return read_float('Please enter a temperature in deg C, or press enter to finish making measurements: ')

def read_resistance(thermistor):
    measured_resistance = thermistor.read_resistance()
    print('Measured thermistor resistance: {}'.format(measured_resistance))
    resistance = read_float(
        'If you\'d like to override this measurement, please enter a different value here, '
        'or press enter to use this measurement, or press Ctrl-D to skip this measurement: '
    )
    if resistance is None:
        resistance = measured_resistance
    return resistance

def collect_measurements(thermistor):
    temperature_resistance_pairs = []
    print(
        'Please enter temperature measurements at steady temperatures.\n'
        'Press Ctrl-D to finish collecting measurements and to compute coefficients.'
    )
    while True:
        print()
        try:
            temperature = read_temperature()
            if temperature is None:
                break
            try:
                resistance = read_resistance(thermistor)
            except EOFError:
                continue
            temperature_resistance_pairs.append((temperature, resistance))
        except EOFError:
            break
    return temperature_resistance_pairs

def main():
    adc = Adafruit_ADS1x15.ADS1115()
    ref_voltage = gpio.AnalogPin(adc, 3)
    bias_resistance = read_bias_resistance()
    thermistor = gpio.Thermistor(
        ref_voltage, gpio.AnalogPin(adc, 0), bias_resistance=bias_resistance
    )

    temperature_resistance_pairs = collect_measurements(thermistor)
    if len(temperature_resistance_pairs) < 3:
        print(
            'Error: At least 3 measurements are required for calibration, '
            'but only {} were collected! Quitting...'
            .format(len(temperature_resistance_pairs))
        )
        return
    print('Computing coefficients using the following measurements:')
    print(temperature_resistance_pairs)
    results = thermistor.calibrate_steinhart_hart(temperature_resistance_pairs)
    print('A: {}'.format(results[0][0]))
    print('B: {}'.format(results[0][1]))
    print('C: {}'.format(results[0][2]))
    print('Residual: {}'.format(results[1]))


if __name__ == '__main__':
    main()
