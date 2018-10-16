import tkinter as tk
import datetime
from picamera import PiCamera
#from scipy import misc

import imaging

led = imaging.DigitalPin(19)
laser = imaging.DigitalPin(26)
x_axis = imaging.StageAxis(23, 24, enable_pin=27)
y_axis = imaging.StageAxis(14, 15, enable_pin=3)
z_axis = imaging.StageAxis(16, 20)
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

    ### create widgets ###
    def create_widgets(self):        

        # x #
        self.label_x = tk.Label(self,text='x')
        self.entry_x_step = tk.Entry(self,width = 5)
        self.entry_x_delay = tk.Entry(self,width = 5)
        self.entry_x_step.insert(0,"512")
        self.entry_x_delay.insert(0,"0.001")
        self.btn_x_forward = tk.Button(self, text="Forward",
                              command=lambda:x_axis.move('f',int(self.entry_x_step.get()),float(self.entry_x_delay.get())))
        self.btn_x_backward = tk.Button(self, text="Backward",
                              command=lambda:x_axis.move('b',int(self.entry_x_step.get()),float(self.entry_x_delay.get())))

        # y #
        self.label_y = tk.Label(self,text='y')
        self.entry_y_step = tk.Entry(self,width = 5)
        self.entry_y_delay = tk.Entry(self,width = 5)
        self.entry_y_step.insert(0,"512")
        self.entry_y_delay.insert(0,"0.001")
        self.btn_y_forward = tk.Button(self, text="Forward",
                              command=lambda:y_axis.move('f',int(self.entry_y_step.get()),float(self.entry_y_delay.get())))
        self.btn_y_backward = tk.Button(self, text="Backward",
                              command=lambda:y_axis.move('b',int(self.entry_y_step.get()),float(self.entry_y_delay.get())))

        # z #
        self.label_z = tk.Label(self,text='z')
        self.entry_z_step = tk.Entry(self,width = 5)
        self.entry_z_delay = tk.Entry(self,width = 5)
        self.entry_z_step.insert(0,"32")
        self.entry_z_delay.insert(0,"0.001")
        self.btn_z_forward = tk.Button(self, text="Forward",
                              command=lambda:z_axis.move('f',int(self.entry_z_step.get()),float(self.entry_z_delay.get())))
        self.btn_z_backward = tk.Button(self, text="Backward",
                              command=lambda:z_axis.move('b',int(self.entry_z_step.get()),float(self.entry_z_delay.get())))

        
        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        self.label_x.grid(row=1,column=0)
        self.entry_x_step.grid(row=1,column=1)
        self.entry_x_delay.grid(row=1,column=2)
        self.btn_x_forward.grid(row=1,column=3)
        self.btn_x_backward.grid(row=1,column=4)
        
        self.label_y.grid(row=2,column=0)
        self.entry_y_step.grid(row=2,column=1)
        self.entry_y_delay.grid(row=2,column=2)
        self.btn_y_forward.grid(row=2,column=3)
        self.btn_y_backward.grid(row=2,column=4)
        
        self.label_z.grid(row=3,column=0)
        self.entry_z_step.grid(row=3,column=1)
        self.entry_z_delay.grid(row=3,column=2)
        self.btn_z_forward.grid(row=3,column=3)
        self.btn_z_backward.grid(row=3,column=4)

        # seperation
        self.label_seperator = tk.Label(self,text='  ')
        self.label_seperator.grid(row=4,column=0)
        
        # shutter speed
        self.label_ss = tk.Label(self,text='SS (ms)')
        self.var_ss = tk.StringVar()
        self.var_ss.trace("w", lambda name, index, mode, var_ss=self.var_ss:ss_update(var_ss))
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
        self.var_ss_bf.trace("w", lambda name, index, mode, var_ss=self.var_ss:ss_update(var_ss))
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
        self.var_ss_fluorescence.trace("w", lambda name, index, mode, var_ss=self.var_ss:ss_update(var_ss))
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

        # autofocus
        self.label_N = tk.Label(self,text='N')
        self.entry_N = tk.Entry(self,width = 5)
        self.label_step = tk.Label(self,text='step')
        self.entry_step = tk.Entry(self,width = 5)
        self.btn_autoFocus = tk.Button(self, text="Autofocus", fg="black",
                                     command=lambda:autofocus(int(self.entry_N.get()),
                                                            int(self.entry_step.get())))
        self.entry_N.insert(0,'15')
        self.entry_step.insert(0,'16')                                                      
        self.label_N.grid(row=12,column=0,sticky=tk.W)
        self.entry_N.grid(row=12,column=1,sticky=tk.W)
        self.label_step.grid(row=12,column=2,sticky=tk.W)
        self.entry_step.grid(row=12,column=3,sticky=tk.W)
        self.btn_autoFocus.grid(row=12,column=4,sticky=tk.W)

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
from time import sleep
import time

# camera control

def ss_update(var_ss):
  try:
    shutter_speed = float(var_ss.get())
    camera.set_shutter_speed(shutter_speed)
  except ValueError:
    pass

# import matplotlib.pyplot as plt

def autofocus(N,step):
  FM = [0]*N
  use_video_port = True
  splitter_port=0
  resize=None
  dt = 0.003
  FM_max = 0
  j = 0
  
  # start_time = time.time()
  prefix = 'Z autofocus, 1080p'

  timestamp = time.time()
  camera.pi_camera.resolution = '1920x1080'
  for i in range(N):
    j = j + 1
    # actuate
    z_axis.move('f',step,0.001)
    sleep(0.005)
    img = np.empty((1920 * 1088 * 3,), dtype=np.uint8)
    #camera.pi_camera.capture(img,'rgb',use_video_port=True)
    led.turn_on()
    camera.pi_camera.capture(img,'rgb',use_video_port=False)
    sleep(0.005)
    led.turn_off()
    # img = misc.imread(filename)
    img = img.reshape(1088,1920,3)
    ROI = img[540-256+1:540+256,960-256+1:960+256,1]
    lap = laplace(ROI)
    fm = mean(square(lap))
    print(fm)
    FM[i] = fm
    #filename = prefix + '_bf_' + str(0).zfill(2) + '_' + str(i).zfill(2) + '_' + str(0).zfill(2) + '.png' 
    #misc.imsave(filename,img)
    FM_max = max(fm,FM_max)
    if fm < FM_max*0.85:
      break

  print('time:')
  print(time.time()-timestamp)
  idx = FM.index(max(FM))
  print(idx)
  # plt.plot(FM)
  z_axis.move('b',step*j,dt)
  z_axis.move('f',step*(idx+1),dt)
  camera.pi_camera.resolution = '1920x1080'
  led.turn_on()
#======================================================================#
#======================================================================#
#======================================================================#

# init.
#led.turn_off()
#laser.turn_off()

camera.pi_camera.start_preview(resolution=(1640, 1232),fullscreen=False, window=(800, 0, 820, 616))

# create GUI
root = tk.Tk()
app = Application(master=root)
app.mainloop()

# exit routine
GPIO.cleanup()
