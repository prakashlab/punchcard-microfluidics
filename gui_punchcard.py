import tkinter as tk
import datetime
import ADS1x15
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
import numpy as np
import time
import atexit

from picamera import PiCamera

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        #self.pack()
        self.grid()
        self.create_widgets()
        # adc = ADS1x15.ADS1115()
        
        
        self.mh = Adafruit_MotorHAT(addr=0x60)
        self.myMotor = self.mh.getMotor(1)
        self.myMotor.setSpeed(150)
        self.Heater1_is_enabled = 0
        self.Heater2_is_enabled = 0
        
        self.updater()

    ### define methods ###
    def toggle_Heater_1(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.btn_Heater1.config(relief='sunken')
            # Heater_1_ON();
            self.Heater1_is_enabled = 1;
        else:
            self.btn_Heater1.config(relief='raised')
            Heater_1_OFF();
            self.Heater1_is_enabled = 0;
            
    def toggle_Heater_2(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.btn_Heater2.config(relief='sunken')
            #Heater_2_ON();
            self.Heater2_is_enabled = 1;
        else:
            self.btn_Heater2.config(relief='raised')
            Heater_2_OFF();
            self.Heater2_is_enabled = 0;
            
    def toggle_Motor(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.btn_Motor.config(relief='sunken')
            self.myMotor.run(Adafruit_MotorHAT.FORWARD)
        else:
            self.btn_Motor.config(relief='raised')
            self.myMotor.run(Adafruit_MotorHAT.RELEASE)
            
    def updater(self):
        A = 0.001125308852122
        B = 0.000234711863267
        C = 0.000000085663516
        
        adc = ADS1x15.ADS1115()
        v0 = 4.096*float(adc.read_adc(2, gain=1))/32767
        v_thermistor1 = 4.096*float(adc.read_adc(0, gain=1))/32767
        if v0-v_thermistor1 > 0:
            R_thermistor1 = v_thermistor1*1962/(v0-v_thermistor1)
            T_thermistor1 = (1/(A + B*np.log(R_thermistor1) + C*(np.log(R_thermistor1))**3)) - 273.15
            #T_thermistor1 = 1/(1/298.15 + (1/3950)*np.log(R_thermistor1/10000)) - 273.15
            self.label_Heater1_Temp.config(text = format(T_thermistor1,'.2f'))
            if T_thermistor1 < float(self.entry_Heater1_SetTemp.get()) and self.Heater1_is_enabled:
            #if T_thermistor1 < float(self.entry_Heater1_SetTemp.get()):
                self.btn_Heater1.config(relief='sunken')
                Heater_1_ON();
            else:
                self.btn_Heater1.config(relief='raised')
                Heater_1_OFF();
        else:
            self.label_Heater1_Temp.config(text = '-')
            
        
        v0 = 4.096*float(adc.read_adc(2, gain=1))/32767
        v_thermistor2 = 4.096*float(adc.read_adc(1, gain=1))/32767
        if v0-v_thermistor2 > 0:
            R_thermistor2 = v_thermistor2*1966/(v0-v_thermistor2)
            T_thermistor2 = (1/(A + B*np.log(R_thermistor2) + C*(np.log(R_thermistor2))**3)) - 273.15
            self.label_Heater2_Temp.config(text = format(T_thermistor2,'.2f'))
            if T_thermistor2 < float(self.entry_Heater2_SetTemp.get()) and self.Heater2_is_enabled:
            # if T_thermistor2 < float(self.entry_Heater2_SetTemp.get()):
                self.btn_Heater2.config(relief='sunken')
                Heater_2_ON();
            else:
                self.btn_Heater2.config(relief='raised')
                Heater_2_OFF();
        else:
            self.label_Heater2_Temp.config(text = '-')
        
            
        self.after(50,self.updater)
        
        

    ### create widgets ###
    def create_widgets(self):        
        # Heater 1 and Heater 2
        self.btn_Heater1 = tk.Button(self, text="Heater 1", fg="black",
                              command=self.toggle_Heater_1)
        self.btn_Heater2 = tk.Button(self, text="Heater 2", fg="black",
                              command=self.toggle_Heater_2)
        self.btn_Motor = tk.Button(self, text="Motor", fg="black",
                              command=self.toggle_Motor)
        
        self.entry_Heater1_SetTemp = tk.Entry(self,width = 5)
        self.entry_Heater2_SetTemp = tk.Entry(self,width = 5)
        self.entry_Heater1_SetTemp.insert(0,"70")
        self.entry_Heater2_SetTemp.insert(0,"40")
        self.label_Heater1_Temp = tk.Label(self, text = '', width = 8)
        self.label_Heater2_Temp = tk.Label(self, text = '', width = 8)
        
        
        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        #self.quit.pack(side="left")

        self.btn_Motor.grid(row=0,column=0)
        self.btn_Heater1.grid(row=1,column=0)
        self.btn_Heater2.grid(row=2,column=0)
        self.entry_Heater1_SetTemp.grid(row=1,column=1)
        self.entry_Heater2_SetTemp.grid(row=2,column=1)
        self.label_Heater1_Temp.grid(row=1,column=2)
        self.label_Heater2_Temp.grid(row=2,column=2)
        

        ###
        # self.label_seperator = tk.Label(self,text='Camera')
        # self.label_seperator.grid(row=4,column=0)
        


### LED, stepper control ###
import RPi.GPIO as GPIO
from time import sleep

# pin def
Heater1_PIN = 4
Heater2_PIN = 17


def initDriver():
	GPIO.setmode(GPIO.BCM)  # set board mode to Broadcom
	
	GPIO.setup(Heater1_PIN, GPIO.OUT)
	GPIO.setup(Heater2_PIN, GPIO.OUT)
	

def Heater_1_ON():
	GPIO.output(Heater1_PIN,1)

def Heater_1_OFF():
	GPIO.output(Heater1_PIN,0)

def Heater_2_ON():
	GPIO.output(Heater2_PIN,1)

def Heater_2_OFF():
	GPIO.output(Heater2_PIN,0)


# init.
initDriver()

def turnOffMotors():
	mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
	mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
 
atexit.register(turnOffMotors)


# create GUI
root = tk.Tk()
app = Application(master=root)
app.mainloop()

# exit routine
GPIO.cleanup()
