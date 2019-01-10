import functools
import tkinter as tk

import gpio


class Application(tk.Frame):
    def __init__(self, led, lasers, master=None):
        self.led = led
        self.lasers = lasers
        self.last_shutter_speed = None
        self.bf = gpio.BinaryState()
        self.bf.after_state_change = self.on_bf_state_change
        self.fluors = [gpio.BinaryState() for laser in self.lasers]
        for (index, fluor) in enumerate(self.fluors):
            fluor.after_state_change = functools.partial(
                self.on_fluor_state_change, index
            )
        super().__init__(master)
        self.grid()
        self.create_widgets()

    ### define methods ###
    def on_led_state_change(self, state):
        if state:
            self.btn_LED.config(relief='sunken')
        else:
            self.btn_LED.config(relief='raised')

    def on_laser_state_change(self, index, state):
        if state:
            self.btns_laser[index].config(relief='sunken')
        else:
            self.btns_laser[index].config(relief='raised')

    def toggle_laser(self, index):
        for (laser_index, laser) in enumerate(self.lasers):
            if laser_index != index:
                self.lasers[laser_index].turn_off()
        self.lasers[index].toggle()

    def on_bf_state_change(self, state):
        if state:
            for fluor in self.fluors:
                fluor.turn_off()
            self.btn_bf.config(relief='sunken')
        else:
            self.btn_bf.config(relief='raised')
        self.led.set_state(state)

    def on_fluor_state_change(self, index, state):
        if state:
            self.bf.turn_off()
            for (fluor_index, fluor) in enumerate(self.fluors):
                if fluor_index != index:
                    fluor.turn_off()
            self.btns_fluor[index].config(relief='sunken')
            self.lasers[index].turn_on()
        else:
            self.btns_fluor[index].config(relief='raised')
            self.lasers[index].turn_off()

    ### create widgets ###

    def create_illumination_widgets(self):
        self.btn_LED = tk.Button(
            self, text='LED', fg='black', command=self.led.toggle
        )
        self.led.after_state_change = self.on_led_state_change
        self.btns_laser = [
            tk.Button(
                self, text='laser {}'.format(index), fg='blue',
                command=functools.partial(self.toggle_laser, index)
            )
            for (index, laser) in enumerate(self.lasers)
        ]
        for (index, laser) in enumerate(self.lasers):
            laser.after_state_change = functools.partial(
                self.on_laser_state_change, index
            )
        self.btn_LED.grid(row=5, column=3)
        for (index, laser) in enumerate(self.lasers):
            self.btns_laser[index].grid(row=5, column=4 + index)

    def create_bf_preset_widgets(self):
        self.btn_bf = tk.Button(
            self, text='Bright Field', fg='black', command=self.bf.toggle
        )
        self.btn_bf.grid(row=7, column=3, columnspan=2)

    def create_fluor_preset_widgets(self, index):
        self.btns_fluor[index] = tk.Button(
            self, text='Fluorescence {}'.format(index), fg='black',
            command=self.fluors[index].toggle
        )
        self.btns_fluor[index].grid(row=8 + index, column=3, columnspan=2)

    def create_widgets(self):
        # quit
        self.quit = tk.Button(
            self, text='QUIT', fg='red', command=root.destroy
        )
        # seperation
        self.label_seperator = tk.Label(self, text='  ')
        self.label_seperator.grid(row=4, column=0)

        # LED and laser
        self.create_illumination_widgets()


if __name__ == '__main__':
    led = gpio.DigitalPin(23)
    lasers = [
        gpio.DigitalPin(17),
        gpio.DigitalPin(27),
        gpio.DigitalPin(22)
    ]

    # create GUI
    root = tk.Tk()
    app = Application(led, lasers, master=root)
    app.mainloop()

    # exit routine
    gpio.cleanup()
