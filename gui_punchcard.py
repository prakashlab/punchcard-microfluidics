import tkinter as tk
import datetime
import Adafruit_ADS1x15
from Adafruit_MotorHAT import Adafruit_MotorHAT
import numpy as np
import time
import atexit

import gpio

heater = gpio.HBridgeDevice(4, 18)
motors = Adafruit_MotorHAT(addr=0x60)
adc = Adafruit_ADS1x15.ADS1115()
ref_voltage = gpio.AnalogPin(adc, 0)
thermistor = gpio.Thermistor(ref_voltage, gpio.AnalogPin(adc, 1))

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        #self.pack()
        self.grid()
        self.create_widgets()

        self.motor = motors.getMotor(1)
        self.motor.setSpeed(150)
        self.heater = heater
        self.heater_setpoint_1_control = False
        self.heater_setpoint_2_control = False

        self.updater()

    ### define methods ###
    def enable_heater_setpoint_1(self):
        self.btn_heater_setpoint_1.config(relief='sunken')
        self.heater_setpoint_1_control = True

    def disable_heater_setpoint_1(self):
        self.btn_heater_setpoint_1.config(relief='raised')
        self.heater_setpoint_1_control = False
        self.btn_heater_setpoint_1.config(fg='black')

    def enable_heater_setpoint_2(self):
        self.btn_heater_setpoint_2.config(relief='sunken')
        self.heater_setpoint_2_control = True

    def disable_heater_setpoint_2(self):
        self.btn_heater_setpoint_2.config(relief='raised')
        self.heater_setpoint_2_control = False
        self.btn_heater_setpoint_2.config(fg='black')

    def enable_motor(self):
        self.btn_motor.config(relief='sunken')
        self.motor.run(Adafruit_MotorHAT.FORWARD)

    def disable_motor(self):
        self.btn_motor.config(relief='raised')
        self.motor.run(Adafruit_MotorHAT.RELEASE)

    def toggle_heater_setpoint_1(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.disable_heater_setpoint_2()
            self.enable_heater_setpoint_1()
        else:
            self.disable_heater_setpoint_1()

    def toggle_heater_setpoint_2(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.disable_heater_setpoint_1()
            self.enable_heater_setpoint_2()
        else:
            self.disable_heater_setpoint_2()

    def toggle_motor(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.enable_motor()
        else:
            self.disable_motor()

    def updater(self):
        A = 0.001125308852122
        B = 0.000234711863267
        C = 0.000000085663516
        heater_setpoint = None
        if self.heater_setpoint_1_control:
            heater_setpoint = float(self.entry_heater_setpoint_1.get())
            btn_heater_setpoint = self.btn_heater_setpoint_1
        elif self.heater_setpoint_2_control:
            heater_setpoint = float(self.entry_heater_setpoint_2.get())
            btn_heater_setpoint = self.btn_heater_setpoint_2

        (thermistor_reading, thermistor_referenced_reading) = thermistor.read(gain=1)
        if thermistor_referenced_reading > 0:
            R_thermistor = thermistor_reading * 1962 / thermistor_referenced_reading # in the code, thermistor had 1966 instead of 1962
            T_thermistor = (1/(A + B*np.log(R_thermistor) + C*(np.log(R_thermistor))**3)) - 273.15
            #T_thermistor = 1/(1/298.15 + (1/3950)*np.log(R_thermistor/10000)) - 273.15
            self.entry_heater_temp.config(text = format(T_thermistor,'.2f'))

            if heater_setpoint is not None:
                if T_thermistor < heater_setpoint:
                    btn_heater_setpoint.config(fg='red')
                    heater.turn_on_forwards()
                else:
                    btn_heater_setpoint.config(fg='blue')
                    heater.turn_off()
            else:
                self.btn_heater_setpoint_1.config(fg='black')
                self.btn_heater_setpoint_2.config(fg='black')
                heater.turn_off()
        else:
            self.entry_heater_temp.config(text = '-')

        self.after(50,self.updater)



    ### create widgets ###
    def create_widgets(self):
        # Heater 1 and Heater 2
        self.btn_heater_setpoint_1 = tk.Button(self, text="Heater Setpoint 1", fg="black",
                              command=self.toggle_heater_setpoint_1)
        self.btn_heater_setpoint_2 = tk.Button(self, text="Heater Setpoint 2", fg="black",
                              command=self.toggle_heater_setpoint_2)
        self.btn_motor = tk.Button(self, text="Motor", fg="black",
                              command=self.toggle_motor)

        self.entry_heater_setpoint_1 = tk.Entry(self,width = 5)
        self.entry_heater_setpoint_2 = tk.Entry(self,width = 5)
        self.entry_heater_setpoint_1.insert(0,"90")
        self.entry_heater_setpoint_2.insert(0,"40")
        self.label_heater_temp = tk.Label(self, text = 'Temperature')
        self.entry_heater_temp = tk.Label(self, text = '?', width = 8)


        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        #self.quit.pack(side="left")

        self.btn_motor.grid(row=0,column=0)
        self.btn_heater_setpoint_1.grid(row=1,column=0)
        self.btn_heater_setpoint_2.grid(row=2,column=0)
        self.entry_heater_setpoint_1.grid(row=1,column=1)
        self.entry_heater_setpoint_2.grid(row=2,column=1)
        self.label_heater_temp.grid(row=3,column=0)
        self.entry_heater_temp.grid(row=3,column=1)

def turnOffMotors():
    for i in range(1, 4 + 1):
        motors.getMotor(i).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)


# create GUI
root = tk.Tk()
app = Application(master=root)
app.mainloop()

# exit routine
gpio.cleanup()
