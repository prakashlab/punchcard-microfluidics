import gpio
from thermal_lysis import (
    run_control_sequence, control_loop_interval,
    preflight_record, postflight_record
)

min_value = 30  # deg C
max_value = 90  # deg C
value_step = 20  # deg C
step_duration = 5  # min
ascending_setpoint_record_sequence = [
    {
        'value': temperature,
        'duration': step_duration,
        'recording': True
    }
    for temperature in range(min_value, max_value + value_step, value_step)
]
descending_setpoint_record_sequence = [
    {
        'value': temperature,
        'duration': step_duration,
        'recording': True
    }
    for temperature in range(max_value, min_value - value_step, -value_step)
]
setpoint_record_sequence = (
    ascending_setpoint_record_sequence
#    + descending_setpoint_record_sequence
)


def main():
    try:
        run_control_sequence(
            setpoint_record_sequence, control_loop_interval,
            'thermal_lysis_test',
            preflight_record=preflight_record,
            postflight_record=postflight_record
        )
    except KeyboardInterrupt:
        print('Quitting early...')
    gpio.cleanup()


if __name__ == '__main__':
    #main()
    pass
