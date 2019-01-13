import tkinter as tk

import gpio
import thermal

adc = gpio.ADC()
thermal_lysis_controller = thermal.HeaterFanController(
    thermal.Thermistor(  # Temperature sensor
        gpio.AnalogPin(adc, 3),  # Reference
        gpio.AnalogPin(adc, 0),  # Sensor
        bias_resistance=1960,  # Ohm
        A=0.0010349722285233954,
        B=0.00022717987892035313,
        C=3.008424040777896e-07
    ),
    thermal.ProportionalControl(  # Heater control
        gain=1.0 / 10.0,  # amount of duty cycle per deg C of error
        setpoint_reached_epsilon=0.5,  # deg C
        output_increases_process_variable=True
    ),
    gpio.PWMPin(18),  # Heater
    thermal.InfiniteGainControl(
        setpoint_reached_epsilon=0.5,  # deg C
        output_increases_process_variable=False
    ),  # Fan control
    gpio.DigitalPin(4),  # Fan
    file_reporter=thermal.ControllerReporter(
        interval=0.5,  # s
        file_prefix='gui_thermal_lysis_'
    ),
    print_reporter=thermal.ControllerPrinter(
        interval=15  # s
    )
)
control_loop_interval = 50  # ms
invalid_temperature_resample_interval = 10  # ms


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # self.pack()
        self.grid()
        self.create_widgets()

        self.heater_setpoint_1 = gpio.BinaryState()
        self.heater_setpoint_1.after_state_change = \
            self.on_heater_setpoint_1_state_change
        self.heater_setpoint_2 = gpio.BinaryState()
        self.heater_setpoint_2.after_state_change = \
            self.on_heater_setpoint_2_state_change

        self.updater()

    # define methods #

    def on_heater_setpoint_1_state_change(self, state):
        if state:
            self.btn_heater_setpoint_1.config(relief='sunken')
            print('Heater setpoint 1 enabled!')
        else:
            self.btn_heater_setpoint_1.config(relief='raised')
            self.btn_heater_setpoint_1.config(fg='black')
            print('Heater setpoint 1 disabled!')
        thermal_lysis_controller.reset()

    def on_heater_setpoint_2_state_change(self, state):
        if state:
            self.btn_heater_setpoint_2.config(relief='sunken')
            print('Heater setpoint 2 enabled!')
        else:
            self.btn_heater_setpoint_2.config(relief='raised')
            self.btn_heater_setpoint_2.config(fg='black')
            print('Heater setpoint 2 disabled!')
        thermal_lysis_controller.reset()

    def toggle_heater_setpoint_1(self):
        self.heater_setpoint_1.toggle()
        if self.heater_setpoint_1.state:
            self.heater_setpoint_2.turn_off()

    def toggle_heater_setpoint_2(self):
        self.heater_setpoint_2.toggle()
        if self.heater_setpoint_2.state:
            self.heater_setpoint_1.turn_off()

    def updater(self):
        setpoint = None
        if self.heater_setpoint_1.state:
            setpoint = float(self.entry_heater_setpoint_1.get())
            btn_heater_setpoint = self.btn_heater_setpoint_1
        elif self.heater_setpoint_2.state:
            setpoint = float(self.entry_heater_setpoint_2.get())
            btn_heater_setpoint = self.btn_heater_setpoint_2
        thermal_lysis_controller.set_setpoint(setpoint)

        if setpoint is None:
            thermal_lysis_controller.file_reporter.file_suffix = \
                '_uncontrolled'
            thermal_lysis_controller.file_reporter.interval = 15
        else:
            thermal_lysis_controller.file_reporter.interval = 0.5
            thermal_lysis_controller.file_reporter.file_suffix = \
                '_setpoint{:.1f}'.format(setpoint)

        (temperature, control_efforts) = thermal_lysis_controller.update()
        heater_control_effort = control_efforts[0]
        if temperature is None:
            self.entry_heater_temp.config(text='-')
            self.after(invalid_temperature_resample_interval, self.updater)
            return

        self.entry_heater_temp.config(text=format(temperature, '.2f'))
        if setpoint is None:
            self.btn_heater_setpoint_1.config(fg='black')
            self.btn_heater_setpoint_2.config(fg='black')
        else:
            btn_heater_setpoint.config(
                fg='red' if heater_control_effort else 'blue'
            )
        self.after(control_loop_interval, self.updater)

    # create widgets #
    def create_widgets(self):
        # Heater 1 and Heater 2
        self.btn_heater_setpoint_1 = tk.Button(
            self, text="Heater Setpoint 1", fg="black",
            command=self.toggle_heater_setpoint_1
        )
        self.btn_heater_setpoint_2 = tk.Button(
            self, text="Heater Setpoint 2", fg="black",
            command=self.toggle_heater_setpoint_2
        )

        self.entry_heater_setpoint_1 = tk.Entry(self, width=5)
        self.entry_heater_setpoint_2 = tk.Entry(self, width=5)
        self.entry_heater_setpoint_1.insert(0, '90')
        self.entry_heater_setpoint_2.insert(0, '40')
        self.label_heater_temp = tk.Label(self, text='Temperature')
        self.entry_heater_temp = tk.Label(self, text='?', width=8)

        # quit
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy)
        # self.quit.pack(side="left")

        self.btn_heater_setpoint_1.grid(row=1, column=0)
        self.btn_heater_setpoint_2.grid(row=2, column=0)
        self.entry_heater_setpoint_1.grid(row=1, column=1)
        self.entry_heater_setpoint_2.grid(row=2, column=1)
        self.label_heater_temp.grid(row=3, column=0)
        self.entry_heater_temp.grid(row=3, column=1)


# create GUI
root = tk.Tk()
app = Application(master=root)
app.mainloop()

# exit routine
gpio.cleanup()
