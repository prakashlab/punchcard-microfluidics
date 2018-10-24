import time

import gpio

heater = gpio.HBridgeDevice(4, 18)
print('Running heater forwards...')
heater.turn_on_forwards()
input('Press enter to continue: ')
print('Running heater in reverse...')
heater.turn_on_backwards()
input('Press enter to quit: ')

gpio.cleanup()
