import argparse
import time

import gpio
import imaging

from picamera import PiCamera

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Timelapse imaging'
    )
    parser.add_argument(
        'prefix', help='Image series filename prefix'
    )
    parser.add_argument(
        '-i', '--interval', help='Timelapse interval (sec)',
        type=int, default=1
    )
    parser.add_argument(
        '-d', '--duration', help='Timelapse duration (sec)',
        type=int, default=30
    )
    args = parser.parse_args()
    prefix = args.prefix
    interval = args.interval
    duration = args.duration

    led = gpio.DigitalPin(19)
    laser = gpio.DigitalPin(26)
    camera = imaging.Camera(
        PiCamera(resolution='3280x2464', sensor_mode=2, framerate=5),
        iso=60, exposure_mode='auto', shutter_speed=200000,
        awb_mode='off', awb_gains=(2, 1)
    )
    led.turn_off()
    laser.turn_off()

    camera.pi_camera.start_preview(
        resolution=(1640, 1232), fullscreen=False, window=(800, 0, 820, 616)
    )

    for i in range(int(duration / interval)):
        try:
            laser.turn_on()
            print('capture', i)
            camera.capture('{}_interval{}s_{}'.format(
                prefix, interval, str(i).zfill(3)
            ))
            laser.turn_off()
            print('  analog gain:', camera.pi_camera.analog_gain)
            print('  digital gain:', camera.pi_camera.digital_gain)
            time.sleep(interval)
        except KeyboardInterrupt:
            print('Quitting!')
            break

    gpio.cleanup()
