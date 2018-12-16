import argparse
import asyncio
import time

from picamera import PiCamera

import picamera_mqtt
from picamera_mqtt import data_path
from picamera_mqtt.deploy import (
    client_config_plain_name, client_configs_path
)
from picamera_mqtt.imaging import imaging
from picamera_mqtt.imaging.mqtt_client_host import Host, topics
from picamera_mqtt.tools import timelapse_host
from picamera_mqtt.util import config
from picamera_mqtt.util.async import (
    register_keyboard_interrupt_signals, run_function
)

import gpio

class IlluminatedTimelapseHost(timelapse_host.TimelapseHost):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lasers = {
            'camera_1': gpio.DigitalPin(17),
            'camera_2': gpio.DigitalPin(27),
            'camera_3': gpio.DigitalPin(22)
        }
        self.images_received = {
            target_name: self.loop.create_future()
            for target_name in self.target_names
        }
        for laser in self.lasers.values():
            laser.turn_off()

    def save_captured_metadata(self, capture):
        super().save_captured_metadata(capture)
        target_name = capture['metadata']['client_name']
        self.images_received[target_name].set_result(True)

    async def run_iteration(self):
        """Run one iteration of the run loop."""
        if not any(self.params_received.values()):
            await asyncio.sleep(timelapse_host.param_receive_poll_interval)
            return

        requested_image = False
        interval_start_time = time.time()
        for target_name in self.target_names:
            if self.image_ids[target_name] <= self.acquisition_length:
                self.lasers[target_name].turn_on()
                self.images_received[target_name] = self.loop.create_future()
                self.request_image(target_name, extra_metadata={
                    'host': 'illuminated_timelapse_host'
                })
                await self.images_received[target_name]
                self.lasers[target_name].turn_off()
                requested_image = True
        interval_end_time = time.time()
        await asyncio.sleep(
            self.acquisition_interval - (interval_end_time - interval_start_time)
        )
        if not requested_image:
            print(
                'No more images to request. Quitting in {} seconds...'
                .format(timelapse_host.final_image_receive_timeout)
            )
            await asyncio.sleep(timelapse_host.final_image_receive_timeout)
            raise asyncio.CancelledError


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Acquire illuminated timelapse series.'
    )
    config.add_config_arguments(
        parser, client_configs_path, client_config_plain_name
    )
    parser.add_argument(
        '--interval', '-i', type=int, default=15,
        help='Image acquisition interval in seconds. Default: 15'
    )
    parser.add_argument(
        '--number', '-n', type=int, default=5,
        help='Number of images to acquire. Default: 5'
    )
    parser.add_argument(
        '--output_dir', '-o', type=str, default=data_path,
        help=(
            'Directory to save captured images and metadata. '
            'Default: {}'.format(data_path)
        )
    )
    args = parser.parse_args()
    acquisition_interval = args.interval
    acquisition_length = args.number
    capture_dir = args.output_dir
    configuration = config.load_config_from_args(args)

    register_keyboard_interrupt_signals()

    print('Starting client...')
    loop = asyncio.get_event_loop()
    mqttc = IlluminatedTimelapseHost(
        loop, **configuration['broker'], **configuration['host'],
        topics=topics, capture_dir=capture_dir,
        acquisition_interval=acquisition_interval,
        acquisition_length=acquisition_length,
        camera_params=configuration['targets']
    )
    run_function(mqttc.run)
    print('Finished!')

    gpio.cleanup()
