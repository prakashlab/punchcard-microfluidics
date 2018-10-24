import tkinter as tk

from picamera import PiCamera

import gpio
import imaging


class Application(tk.Frame):
    def __init__(self, led, laser, camera, master=None):
        self.led = led
        self.laser = laser
        self.camera = camera
        super().__init__(master)
        #self.pack()
        self.grid()
        self.create_widgets()

    ### define methods ###
    def enable_led(self):
        self.btn_LED.config(relief='sunken')
        self.led.turn_on()

    def disable_led(self):
          self.btn_LED.config(relief='raised')
          self.led.turn_off()

    def enable_laser(self):
          self.btn_laser.config(relief='sunken')
          self.laser.turn_on()

    def disable_laser(self):
        self.btn_laser.config(relief='raised')
        self.laser.turn_off()

    def toggle_led(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.enable_led()
        else:
            self.disable_led()

    def toggle_laser(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.enable_laser()
        else:
            self.disable_laser()

    def toggle_bf(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.disable_laser()
            self.btn_fluor.config(relief='raised')
            self.btn_bf.config(relief='sunken')
            self.var_ss.set(self.var_ss_bf.get())
            self.enable_led()
        else:
            self.btn_bf.config(relief='raised')
            self.disable_led()

    def toggle_fluor(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.disable_led()
            self.btn_fluor.config(relief='sunken')
            self.btn_bf.config(relief='raised')
            self.var_ss.set(self.var_ss_fluor.get())
            self.enable_laser()
        else:
            self.btn_fluor.config(relief='raised')
            self.disable_laser()

    def set_shutter_speed(self):
        try:
            shutter_speed = float(self.var_ss.get())
            self.camera.set_shutter_speed(shutter_speed)
        except ValueError:
            pass

    ### create widgets ###
    def create_shutter_speed_widgets(self):
        self.label_ss = tk.Label(self, text='SS (ms)')
        self.var_ss = tk.StringVar()
        self.var_ss.trace(
            'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss = tk.Entry(self, width=6,textvariable=self.var_ss)
        self.entry_ss.insert(0, '2')
        self.label_ss.grid(row=5, column=0, sticky=tk.W)
        self.entry_ss.grid(row=5, column=1, sticky=tk.W)

    def create_illumination_widgets(self):
        self.btn_LED = tk.Button(
            self, text='LED', fg='black', command=self.toggle_led
        )
        self.btn_laser = tk.Button(
            self, text='laser', fg='blue', command=self.toggle_laser
        )
        self.btn_LED.grid(row=5, column=3)
        self.btn_laser.grid(row=5, column=4)

    def create_bf_preset_widgets(self):
        self.label_ss_bf = tk.Label(self, text='SS (ms)')
        self.var_ss_bf = tk.StringVar()
        self.var_ss_bf.trace(
            'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss_bf = tk.Entry(self, width = 6, textvariable=self.var_ss_bf)
        self.entry_ss_bf.insert(0, '2')
        self.btn_bf = tk.Button(
            self, text='Bright Field', fg='black', command=self.toggle_bf
        )
        self.label_ss_bf.grid(row=7, column=0, sticky=tk.W)
        self.entry_ss_bf.grid(row=7, column=1, sticky=tk.W)
        self.btn_bf.grid(row=7, column=3, columnspan=2)

    def create_fluor_preset_widgets(self):
          self.label_ss_fluor = tk.Label(self,text='SS (ms)')
          self.var_ss_fluor = tk.StringVar()
          self.var_ss_fluor.trace(
              'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
          )
          self.entry_ss_fluor = tk.Entry(
              self, width=6, textvariable=self.var_ss_fluor
          )
          self.entry_ss_fluor.insert(0, '200')
          self.btn_fluor = tk.Button(
              self, text='Fluorescence', fg='black', command=self.toggle_fluor
          )
          self.label_ss_fluor.grid(row=8, column=0, sticky=tk.W)
          self.entry_ss_fluor.grid(row=8, column=1, sticky=tk.W)
          self.btn_fluor.grid(row=8, column=3, columnspan=2)

    def create_zoom_widgets(self):
          self.label_zoom = tk.Label(self,text='Zoom')
          self.scale_zoom = tk.Scale(
              self, from_=1, to=10, resolution=1, orient=tk.HORIZONTAL,
              length=275, command=lambda value:self.camera.set_roi(float(value))
          )
          self.scale_zoom.set(1)
          self.label_zoom.grid(row=10, column=0, sticky=tk.W)
          self.scale_zoom.grid(row=10, column=1, columnspan=4, sticky=tk.W)

    def create_capture_widgets(self):
          # filename
          self.label_filename = tk.Label(self, text='Prefix')
          self.entry_filename = tk.Entry(self, width=31)
          self.label_filename.grid(row=12, column=0, sticky=tk.W)
          self.entry_filename.grid(row=12, column=1, columnspan=4, sticky=tk.W)
          # capture
          self.btn_capture = tk.Button(
              self, text='Capture', fg='black', bg='yellow', width=32, height=2,
              command=lambda: self.camera.capture('{}_{}x_{}us'.format(
                  self.entry_filename.get(), int(self.scale_zoom.get()),
                  self.entry_ss.get()
              ))
          )
          self.btn_capture.grid(row=13, column=0, columnspan=5, rowspan=2)

    def create_widgets(self):
          # quit
          self.quit = tk.Button(self, text='QUIT', fg='red', command=root.destroy)
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
          self.create_fluor_preset_widgets()

          # seperation
          self.label_seperator = tk.Label(self, text='  ')
          self.label_seperator.grid(row=9, column=0)

          # zoom
          self.create_zoom_widgets()

          # seperation
          self.label_seperator = tk.Label(self, text='  ')
          self.label_seperator.grid(row=11, column=0)

          # capture
          self.create_capture_widgets()


if __name__ == '__main__':
    led = gpio.DigitalPin(22)
    laser = gpio.DigitalPin(17)
    camera = imaging.Camera(
        PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
        # PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
        # PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
        iso=60, exposure_mode='off', shutter_speed=500,
        awb_mode='off', awb_gains=(2, 1)
    )

    camera.pi_camera.start_preview(
        resolution=(1640, 1232),fullscreen=False, window=(800, 0, 820, 616)
    )

    # create GUI
    root = tk.Tk()
    app = Application(led, laser, camera, master=root)
    app.mainloop()

    # exit routine
    gpio.cleanup()
