import time

import gpio
import thermal


# Reporting settings
setpoint_reached_epsilon = 0.5  # deg C
file_reporter_interval = 0.5
print_reporter_interval = 15  # s

# Controller initialization
adc = gpio.ADC()
controller = thermal.HeaterFanController(
    thermal.Thermistor(  # Temperature sensor
        gpio.AnalogPin(adc, 3),  # Reference
        gpio.AnalogPin(adc, 0),  # Sensor
        bias_resistance=1960,  # Ohm
        A=0.0010349722285233954,
        B=0.00022717987892035313,
        C=3.008424040777896e-07
    ),
    thermal.PIDControl(  # Heater control
        0.0775, 0.00125, 0.0,  # Kp, Ki, Kd
        setpoint_reached_epsilon=setpoint_reached_epsilon,
        proportional_on_measurement=True
    ),
    gpio.PWMPin(18),  # Heater
    thermal.InfiniteGainControl(
        setpoint_reached_epsilon=setpoint_reached_epsilon,
        output_increases_process_variable=False
    ),  # Fan control
    gpio.DigitalPin(4),  # Fan
    fan_setpoint_offset=0.25,  # deg C
    file_reporter=thermal.ControllerReporter(
        interval=file_reporter_interval,
        file_prefix='thermal_lysis_'
    ),
    print_reporter=thermal.ControllerPrinter(
        interval=print_reporter_interval
    )
)

# Setpoint sequence settings
control_loop_interval = 50  # ms
room_temperature = 25.0  # deg C
lysis_temperature = 90.0  # deg C
lysis_duration = 10.0  # deg C
rpa_prep_temperature = 40.0  # deg C
rpa_prep_hold_demo_duration = 10.0  # min; specify None to hold until Ctrl+C

# Setpoint sequence initialization
preflight_record = {
    'value': room_temperature,  # deg C
    'duration': 0,  # min
    'recording': False
}
postflight_record = {
    'value': room_temperature,
    'duration': 0,  # min
    'recording': False
}
setpoint_record_sequence = [
    {
        'value': lysis_temperature,
        'duration': lysis_duration,
        'recording': True
    },
    {
        'value': rpa_prep_temperature,
        'duration': rpa_prep_hold_demo_duration,
        'recording': True
    },
]


def run_controller_record(controller, control_loop_interval, setpoint_record):
    controller.reset()
    setpoint = setpoint_record['value']
    recording = setpoint_record['recording']
    duration = setpoint_record['duration']
    if controller.file_reporter is not None:
        controller.file_reporter.file_suffix = '_setpoint{:.1f},{:.1f}'.format(
            setpoint, duration
        )

    controller.set_setpoint(setpoint)
    print('Setpoint is now {:.1f}...'.format(setpoint))
    if recording:
        controller.enable_reporters()
    else:
        controller.disable_reporters()

    # Control to setpoint
    while not controller.setpoint_reached:
        controller.update()
        time.sleep(control_loop_interval / 1000)
    # Control to duration
    print('Reached setpoint!')
    setpoint_reached_time = time.time()
    if duration is None:
        print(
            'Holding at setpoint indefinitely. '
            'Press Ctrl+C to stop holding and quit.'
        )
    else:
        print('Holding for {:.1f} min...'.format(duration))

    while (
        duration is None or time.time() - setpoint_reached_time < 60 * duration
    ):
        controller.update()
        time.sleep(control_loop_interval / 1000)


def run_controller_sequence(
        controller, control_loop_interval, setpoint_record_sequence
):
    for setpoint_record in setpoint_record_sequence:
        run_controller_record(
            controller, control_loop_interval, setpoint_record
        )
    print('Finished!')


def run_control_sequence(
    setpoint_record_sequence, control_loop_interval, sequence_name,
    preflight_record=None, postflight_record=None
):
    controller.file_reporter.file_prefix = '{}_'.format(sequence_name)
    # Build sequence reporter
    sequence_string = '-'.join(
        '{:.1f},{:.1f}'.format(
            setpoint_record['value'], setpoint_record['duration']
        )
        for setpoint_record in setpoint_record_sequence
    )
    sequence_reporter = thermal.ControllerReporter(
        interval=file_reporter_interval,
        file_prefix='{}_'.format(sequence_name),
        file_suffix='_setpoints{}'.format(sequence_string)
    )
    sequence_reporter.control_efforts = controller.output_effort_names
    controller.reporters.insert(0, sequence_reporter)
    controller.enable_reporters()
    controller.disableable_reporters = [
        controller.file_reporter, sequence_reporter
    ]
    # Preflight
    if preflight_record is not None:
        print('Preflight: controlling system to starting temperature.')
        if controller.process_variable.read() > preflight_record['value']:
            controller.heater_control.disable()
        else:
            controller.heater_control.enable()
        run_controller_record(
            controller, control_loop_interval, preflight_record
        )
        sequence_reporter.reset()
    # Run sequence
    controller.heater_control.enable()
    run_controller_sequence(
        controller, control_loop_interval, setpoint_record_sequence
    )
    # Postflight
    # Note: assumes that only the fan is needed to reach postflight setpoint.
    if postflight_record is not None:
        print('Postflight: controlling system to ending temperature.')
        if controller.process_variable.read() > postflight_record['value']:
            controller.heater_control.disable()
        else:
            controller.heater_control.enable()
        run_controller_record(
            controller, control_loop_interval, postflight_record
        )


def main():
    try:
        run_control_sequence(
            setpoint_record_sequence, control_loop_interval, 'thermal_lysis',
            preflight_record=preflight_record,
            postflight_record=postflight_record
        )
    except KeyboardInterrupt:
        print('Quitting early...')
    gpio.cleanup()


if __name__ == '__main__':
    main()
