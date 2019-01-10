import gpio

heater = gpio.DigitalPin(4)
print('Running heater...')
heater.turn_on()
input('Press enter to quit: ')

gpio.cleanup()
