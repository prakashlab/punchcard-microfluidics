import functools
import tkinter as tk

import gpio

from picamera import PiCamera

import picamera_mqtt
from picamera_mqtt.imaging import imaging


class Application(tk.Frame):
    def __init__(self, led, lasers, camera, master=None):
        self.led = led
        self.lasers = lasers
        self.camera = camera
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
            self.var_ss.set(self.var_ss_bf.get())
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
            self.var_ss.set(self.vars_ss_fluor[index].get())
            self.lasers[index].turn_on()
        else:
            self.btns_fluor[index].config(relief='raised')
            self.lasers[index].turn_off()

    def set_shutter_speed(self):
        try:
            shutter_speed = float(self.var_ss.get())
            if self.last_shutter_speed == shutter_speed:
                return
            self.camera.set_shutter_speed(shutter_speed)
            self.last_shutter_speed = shutter_speed
        except ValueError:
            pass

    ### create widgets ###
    def create_shutter_speed_widgets(self):
        self.label_ss = tk.Label(self, text='SS (ms)')
        self.var_ss = tk.StringVar()
        self.var_ss.trace(
            'w', lambda name, index, mode,
            var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss = tk.Entry(self, width=6,textvariable=self.var_ss)
        self.entry_ss.insert(0, '2')
        self.label_ss.grid(row=5, column=0, sticky=tk.W)
        self.entry_ss.grid(row=5, column=1, sticky=tk.W)

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
        self.label_ss_bf = tk.Label(self, text='SS (ms)')
        self.var_ss_bf = tk.StringVar()
        self.var_ss_bf.trace(
            'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss_bf = tk.Entry(self, width=6, textvariable=self.var_ss_bf)
        self.entry_ss_bf.insert(0, '2')
        self.btn_bf = tk.Button(
            self, text='Bright Field', fg='black', command=self.bf.toggle
        )
        self.label_ss_bf.grid(row=7, column=0, sticky=tk.W)
        self.entry_ss_bf.grid(row=7, column=1, sticky=tk.W)
        self.btn_bf.grid(row=7, column=3, columnspan=2)

    def create_fluor_preset_widgets(self, index):
        label_ss_fluor = tk.Label(self, text='SS (ms)')
        self.vars_ss_fluor[index] = tk.StringVar()
        self.vars_ss_fluor[index].trace(
            'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entries_ss_fluor[index] = tk.Entry(
            self, width=6, textvariable=self.vars_ss_fluor[index]
        )
        self.entries_ss_fluor[index].insert(0, '200')
        self.btns_fluor[index] = tk.Button(
            self, text='Fluorescence {}'.format(index), fg='black',
            command=self.fluors[index].toggle
        )
        label_ss_fluor.grid(row=8 + index, column=0, sticky=tk.W)
        self.entries_ss_fluor[index].grid(row=8 + index, column=1, sticky=tk.W)
        self.btns_fluor[index].grid(row=8 + index, column=3, columnspan=2)

    def create_zoom_widgets(self):
        self.label_zoom = tk.Label(self, text='Zoom')
        self.scale_zoom = tk.Scale(
            self, from_=1, to=10, resolution=1, orient=tk.HORIZONTAL,
            length=275, command=lambda value: self.camera.set_roi(float(value))
        )
        self.scale_zoom.set(1)
        self.label_zoom.grid(row=10 + len(self.lasers), column=0, sticky=tk.W)
        self.scale_zoom.grid(
            row=10 + len(self.lasers), column=1, columnspan=4, sticky=tk.W
        )

    def create_capture_widgets(self):
        # filename
        self.label_filename = tk.Label(self, text='Prefix')
        self.entry_filename = tk.Entry(self, width=31)
        self.label_filename.grid(
            row=12 + len(self.lasers), column=0, sticky=tk.W
        )
        self.entry_filename.grid(
            row=12 + len(self.lasers), column=1, columnspan=4, sticky=tk.W
        )
        # capture
        self.btn_capture = tk.Button(
            self, text='Capture', fg='black', bg='yellow', width=32, height=2,
            command=lambda: self.camera.capture('{}_{}x_{}us'.format(
                self.entry_filename.get(), int(self.scale_zoom.get()),
                self.entry_ss.get()
            ))
        )
        self.btn_capture.grid(
            row=13 + len(self.lasers), column=0, columnspan=5, rowspan=2
        )

    def create_widgets(self):
        # quit
        self.quit = tk.Button(
            self, text='QUIT', fg='red', command=root.destroy
        )
        # seperation
        self.label_seperator = tk.Label(self, text='  ')
        self.label_seperator.grid(row=4, column=0)

        # shutter speed
        self.create_shutter_speed_widgets()

        # LED and laser
        self.create_illumination_widgets()

        # seperation
        self.label_seperator = tk.Label(self, text='  ')
        self.label_seperator.grid(row=6, column=0)

        # preset modes
        self.create_bf_preset_widgets()
        self.entries_ss_fluor = [None for laser in self.lasers]
        self.vars_ss_fluor = [None for laser in self.lasers]
        self.btns_fluor = [None for laser in self.lasers]
        for (index, laser) in enumerate(self.lasers):
            self.create_fluor_preset_widgets(index)

        # seperation
        self.label_seperator = tk.Label(self, text='  ')
        self.label_seperator.grid(row=9 + len(self.lasers), column=0)

        # zoom
        self.create_zoom_widgets()

        # seperation
        self.label_seperator = tk.Label(self, text='  ')
        self.label_seperator.grid(row=11 + len(self.lasers), column=0)

        # capture
        self.create_capture_widgets()


if __name__ == '__main__':
    led = gpio.DigitalPin(23)
    lasers = [
        gpio.DigitalPin(17),
        gpio.DigitalPin(27),
        gpio.DigitalPin(22)
    ]
    camera = imaging.Camera(
        PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
        iso=60, exposure_mode='off', shutter_speed=500,
        awb_mode='off', awb_gains=(2, 1)
    )

    camera.pi_camera.start_preview(
        resolution=(1640, 1232), fullscreen=False, window=(800, 0, 820, 616)
    )

    # create GUI
    root = tk.Tk()
    app = Application(led, lasers, camera, master=root)
    app.mainloop()

    # exit routine
    gpio.cleanup()
