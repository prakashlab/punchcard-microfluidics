import time

import gpio
import thermal

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
        setpoint_reached_epsilon=0.5,  # deg C
        proportional_on_measurement=True
    ),
    gpio.PWMPin(18),  # Heater
    thermal.InfiniteGainControl(
        setpoint_reached_epsilon=0.5,  # deg C
        output_increases_process_variable=False
    ),  # Fan control
    gpio.DigitalPin(4),  # Fan
    fan_setpoint_offset=0.25,  # deg C
    file_reporter=thermal.ControllerReporter(
        interval=0.5,  # s
        file_prefix='thermal_lysis_'
    ),
    print_reporter=thermal.ControllerPrinter(
        interval=15  # s
    )
)
control_loop_interval = 50  # ms
setpoint_records = [
    {
        'value': 90.0,  # deg C
        'duration': 10.0,  # min
        'recording': True
    },
    {
        'value': 40.0,  # deg C
        'duration': 10.0,  # min
        'recording': True
    },
    {
        'value': 27.0,  # deg C
        'duration': 0,  # min
        'recording': False
    }
]


def run_controller(controller, control_loop_interval, setpoint_records):
    for setpoint_record in setpoint_records:
        setpoint = setpoint_record['value']
        recording = setpoint_record['recording']
        duration = setpoint_record['duration']
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
            time.sleep(control_loop_interval)
        # Control to duration
        print('Reached setpoint! Holding for {:.1f} min...'.format(duration))
        setpoint_reached_time = time.time()
        while (
            duration is None or time.time() - setpoint_reached_time < duration
        ):
            controller.update()
            time.sleep(control_loop_interval)
        controller.reset()

def main():
    sequence_string = '-'.join(
        '{:.1f},{:.1f}'.format(
            setpoint_record['value'], setpoint_record['duration']
        )
        for setpoint_record in setpoint_records
    )
    sequence_reporter = thermal.ControllerReporter(
        interval=0.5,  # s
        file_suffix='_setpoints{}'.format(sequence_string)
    )
    controller.reporters.append(sequence_reporter)
    controller.disableable_reporters = [
        controller.file_reporter, controller.sequence_reporter
    ]
    run_controller(controller, control_loop_interval, setpoint_records)


if __name__ == '__main__':
    main()
