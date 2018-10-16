import tkinter as tk
import datetime
import Adafruit_ADS1x15
from Adafruit_MotorHAT import Adafruit_MotorHAT
import numpy as np
import time
import atexit

import gpio

heater_1 = gpio.DigitalPin(4)
heater_2 = gpio.DigitalPin(17)
motors = Adafruit_MotorHAT(addr=0x60)
adc = Adafruit_ADS1x15.ADS1115()
ref_voltage = gpio.AnalogPin(adc, 2)
thermistor_1 = gpio.Thermistor(ref_voltage, gpio.AnalogPin(adc, 0))
thermistor_2 = gpio.Thermistor(ref_voltage, gpio.AnalogPin(adc, 1))

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        #self.pack()
        self.grid()
        self.create_widgets()
        # adc = Adafruit_ADS1x15.ADS1115()

        self.motor = motors.getMotor(1)
        self.motor.setSpeed(150)
        self.heater_1_control = False
        self.heater_2_control = False

        self.updater()

    ### define methods ###
    def enable_heater_1(self):
        self.btn_heater_1.config(relief='sunken')
        self.heater_1_control = True

    def disable_heater_1(self):
        self.btn_heater_1.config(relief='raised')
        heater_1.turn_off()
        self.heater_1_control = False

    def enable_heater_2(self):
        self.btn_heater_2.config(relief='sunken')
        self.heater_2_control = True

    def disable_heater_2(self):
        self.btn_heater_2.config(relief='raised')
        heater_2.turn_off()
        self.heater_2_control = False

    def enable_motor(self):
        self.btn_motor.config(relief='sunken')
        self.motor.run(Adafruit_MotorHAT.FORWARD)

    def disable_motor(self):
        self.btn_motor.config(relief='raised')
        self.motor.run(Adafruit_MotorHAT.RELEASE)

    def toggle_heater_1(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.enable_heater_1()
        else:
            self.disable_heater_1()

    def toggle_heater_2(self,tog=[0]):
        tog[0] = not tog[0]
        if tog[0]:
            self.enable_heater_2()
        else:
            self.disable_heater_2()

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

        adc = Adafruit_ADS1x15.ADS1115()
        (thermistor_1_reading, thermistor_1_referenced_reading) = thermistor_1.read(gain=1)
        if thermistor_1_referenced_reading > 0:
            R_thermistor1 = thermistor_1_reading * 1962 / thermistor_1_referenced_reading
            T_thermistor1 = (1/(A + B*np.log(R_thermistor1) + C*(np.log(R_thermistor1))**3)) - 273.15
            #T_thermistor1 = 1/(1/298.15 + (1/3950)*np.log(R_thermistor1/10000)) - 273.15
            self.label_heater_1_Temp.config(text = format(T_thermistor1,'.2f'))
            if T_thermistor1 < float(self.entry_heater_1_SetTemp.get()) and self.heater_1_control:
            #if T_thermistor1 < float(self.entry_heater_1_SetTemp.get()):
                self.btn_heater_1.config(relief='sunken')
                heater_1.turn_on()
            else:
                self.btn_heater_1.config(relief='raised')
                heater_1.turn_off()
        else:
            self.label_heater_1_Temp.config(text = '-')


        v0 = ref_voltage.read()
        (thermistor_2_reading, thermistor_2_referenced_reading) = thermistor_2.read(gain=1)
        if thermistor_2_referenced_reading > 0:
            R_thermistor2 = thermistor_1_reading * 1966  / thermistor_2_referenced_reading
            T_thermistor2 = (1/(A + B*np.log(R_thermistor2) + C*(np.log(R_thermistor2))**3)) - 273.15
            self.label_heater_2_Temp.config(text = format(T_thermistor2,'.2f'))
            if T_thermistor2 < float(self.entry_heater_2_SetTemp.get()) and self.heater_2_control:
            # if T_thermistor2 < float(self.entry_heater_2_SetTemp.get()):
                self.btn_heater_2.config(relief='sunken')
                heater_2.turn_on()
            else:
                self.btn_heater_2.config(relief='raised')
                heater_2.turn_off()
        else:
            self.label_heater_2_Temp.config(text = '-')


        self.after(50,self.updater)



    ### create widgets ###
    def create_widgets(self):
        # Heater 1 and Heater 2
        self.btn_heater_1 = tk.Button(self, text="Heater 1", fg="black",
                              command=self.toggle_heater_1)
        self.btn_heater_2 = tk.Button(self, text="Heater 2", fg="black",
                              command=self.toggle_heater_2)
        self.btn_motor = tk.Button(self, text="Motor", fg="black",
                              command=self.toggle_motor)

        self.entry_heater_1_SetTemp = tk.Entry(self,width = 5)
        self.entry_heater_2_SetTemp = tk.Entry(self,width = 5)
        self.entry_heater_1_SetTemp.insert(0,"70")
        self.entry_heater_2_SetTemp.insert(0,"40")
        self.label_heater_1_Temp = tk.Label(self, text = '', width = 8)
        self.label_heater_2_Temp = tk.Label(self, text = '', width = 8)


        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        #self.quit.pack(side="left")

        self.btn_motor.grid(row=0,column=0)
        self.btn_heater_1.grid(row=1,column=0)
        self.btn_heater_2.grid(row=2,column=0)
        self.entry_heater_1_SetTemp.grid(row=1,column=1)
        self.entry_heater_2_SetTemp.grid(row=2,column=1)
        self.label_heater_1_Temp.grid(row=1,column=2)
        self.label_heater_2_Temp.grid(row=2,column=2)

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
