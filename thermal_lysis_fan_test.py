import gpio

fan = gpio.DigitalPin(4)
print('Running fans...')
fan.turn_on()
input('Press enter to quit: ')

gpio.cleanup()
