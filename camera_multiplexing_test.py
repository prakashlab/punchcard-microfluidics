from picamera import PiCamera

import gpio
import imaging

if __name__ == '__main__':
    multiplexer = gpio.CameraMultiplexer()

    input('Press enter to switch to camera a: ')
    multiplexer.camera_a()
    camera = imaging.Camera(
        PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
        iso=60, exposure_mode='off', shutter_speed=500,
        awb_mode='off', awb_gains=(2, 1)
    )

    camera.pi_camera.start_preview(
        resolution=(1640, 1232), fullscreen=False, window=(800, 0, 820, 616)
    )

    input('Press enter to switch to camera b: ')
    multiplexer.camera_b()
    input('Press enter to switch to camera c: ')
    multiplexer.camera_c()
    input('Press enter to switch to no camera: ')
    multiplexer.no_camera()
