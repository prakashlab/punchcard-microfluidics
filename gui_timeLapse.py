import tkinter as tk

from picamera import PiCamera

import imaging

led = imaging.DigitalPin(19)
laser = imaging.DigitalPin(26)
camera = imaging.Camera(
  PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
  # PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
  # PiCamera(resolution='3280x2464', sensor_mode=2, framerate=15),
  iso=60, exposure_mode='off', shutter_speed=500,
  awb_mode='off', awb_gains=(2, 1)
)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        #self.pack()
        self.grid()
        self.create_widgets()

    ### define methods ###
    def toggle_LED(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.btn_LED.config(relief='sunken')
            led.turn_on()
        else:
            self.btn_LED.config(relief='raised')
            led.turn_off()

    def toggle_laser(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.btn_laser.config(relief='sunken')
            laser.turn_on()
        else:
            self.btn_laser.config(relief='raised')
            laser.turn_off()

    def toggle_bf(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            laser.turn_off()
            self.btn_laser.config(relief='raised')
            self.btn_fluorescence.config(relief='raised')
            self.var_ss.set(self.var_ss_bf.get())
            self.btn_LED.config(relief='sunken')
            self.btn_bf.config(relief='sunken')
            led.turn_on()
        else:
            self.btn_LED.config(relief='raised')
            self.btn_bf.config(relief='raised')
            led.turn_off()

    def toggle_fluorescence(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            led.turn_off()
            self.btn_LED.config(relief='raised')
            self.btn_bf.config(relief='raised')
            self.var_ss.set(self.var_ss_fluorescence.get())
            self.btn_laser.config(relief='sunken')
            self.btn_fluorescence.config(relief='sunken')
            laser.turn_on()
        else:
            self.btn_laser.config(relief='raised')
            self.btn_fluorescence.config(relief='raised')
            laser.turn_off()

    def set_shutter_speed(self):
      try:
        shutter_speed = float(self.var_ss.get())
        camera.set_shutter_speed(shutter_speed)
      except ValueError:
        pass

    ### create widgets ###
    def create_widgets(self):
        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=4,column=0)

        # shutter speed
        self.label_ss = tk.Label(self,text='SS (ms)')
        self.var_ss = tk.StringVar()
        self.var_ss.trace(
          'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss = tk.Entry(self,width = 6,textvariable=self.var_ss)
        self.entry_ss.insert(0,"2")
        self.label_ss.grid(row=5,column=0,sticky=tk.W)
        self.entry_ss.grid(row=5,column=1,sticky=tk.W)

        # LED and laser
        self.btn_LED = tk.Button(self, text="LED", fg="black",
                              command=self.toggle_LED)
        self.btn_laser = tk.Button(self, text="laser", fg="blue",
                              command=self.toggle_laser)
        self.btn_LED.grid(row=5,column=3)
        self.btn_laser.grid(row=5,column=4)

        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=6,column=0)

        # preset modes - bf
        self.label_ss_bf = tk.Label(self,text='SS (ms)')
        self.var_ss_bf = tk.StringVar()
        self.var_ss_bf.trace(
          'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss_bf = tk.Entry(self,width = 6,textvariable=self.var_ss_bf)
        self.entry_ss_bf.insert(0,"2")
        self.btn_bf = tk.Button(self, text="Bright Field", fg="black",
                              command=self.toggle_bf)
        self.label_ss_bf.grid(row=7,column=0,sticky=tk.W)
        self.entry_ss_bf.grid(row=7,column=1,sticky=tk.W)
        self.btn_bf.grid(row=7,column=3,columnspan=2)

        # preset modes - fluorescence
        self.label_ss_fluorescence = tk.Label(self,text='SS (ms)')
        self.var_ss_fluorescence = tk.StringVar()
        self.var_ss_fluorescence.trace(
          'w', lambda name, index, mode, var_ss=self.var_ss: self.set_shutter_speed()
        )
        self.entry_ss_fluorescence = tk.Entry(self,width = 6,textvariable=self.var_ss_fluorescence)
        self.entry_ss_fluorescence.insert(0,"200")
        self.btn_fluorescence = tk.Button(self, text="Fluorescence", fg="black",
                              command=self.toggle_fluorescence)
        self.label_ss_fluorescence.grid(row=8,column=0,sticky=tk.W)
        self.entry_ss_fluorescence.grid(row=8,column=1,sticky=tk.W)
        self.btn_fluorescence.grid(row=8,column=3,columnspan=2)

        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=9,column=0)

        # zoom
        self.label_zoom = tk.Label(self,text='Zoom')
        self.scale_zoom = tk.Scale(self,from_=1, to = 10,
                                  resolution=1,
                                  orient=tk.HORIZONTAL,
                                  length = 275,
                                  command=lambda value:camera.set_roi(float(value)))
        self.scale_zoom.set(1)
        self.label_zoom.grid(row=10,column=0,sticky=tk.W)
        self.scale_zoom.grid(row=10,column=1,columnspan=4,sticky=tk.W)

        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=11,column=0)

        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=13,column=0)

        # filename
        self.label_filename = tk.Label(self,text='Prefix')
        self.entry_filename = tk.Entry(self,width = 31)

        self.label_filename.grid(row=14,column=0,sticky=tk.W)
        self.entry_filename.grid(row=14,column=1,columnspan=4,sticky=tk.W)

        # capture
        self.btn_capture = tk.Button(
          self, text="Capture", fg="black", bg = "yellow", width = 32, height = 2,
          command=lambda:camera.capture(
            self.entry_filename.get(), self.entry_ss.get(), self.scale_zoom.get()
          )
        )
        self.btn_capture.grid(row=15,column=0,columnspan=5,rowspan=2)

### LED, stepper control ###
import RPi.GPIO as GPIO

# init
#led.turn_off()
#laser.turn_off()

camera.pi_camera.start_preview(resolution=(1640, 1232),fullscreen=False, window=(800, 0, 820, 616))

# create GUI
root = tk.Tk()
app = Application(master=root)
app.mainloop()

# exit routine
GPIO.cleanup()
