import time

import gpio

heater = gpio.DigitalPin(18)
print('Running heater...')
heater.turn_on()
input('Press enter to quit: ')

gpio.cleanup()
