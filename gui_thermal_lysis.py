import tkinter as tk

import gpio
from thermal_lysis import controller

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
        controller.reset()

    def on_heater_setpoint_2_state_change(self, state):
        if state:
            self.btn_heater_setpoint_2.config(relief='sunken')
            print('Heater setpoint 2 enabled!')
        else:
            self.btn_heater_setpoint_2.config(relief='raised')
            self.btn_heater_setpoint_2.config(fg='black')
            print('Heater setpoint 2 disabled!')
        controller.reset()

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
        controller.set_setpoint(setpoint)

        if setpoint is None:
            controller.file_reporter.file_suffix = \
                '_uncontrolled'
            controller.file_reporter.interval = 15
        else:
            controller.file_reporter.interval = 0.5
            controller.file_reporter.file_suffix = \
                '_setpoint{:.1f}'.format(setpoint)

        (temperature, control_efforts) = controller.update()
        (heater_control_effort, fan_control_effort) = control_efforts
        if temperature is None:
            self.entry_heater_temp.config(text='-')
            self.after(invalid_temperature_resample_interval, self.updater)
            return

        self.entry_heater_temp.config(text=format(temperature, '.2f'))
        if setpoint is None:
            self.btn_heater_setpoint_1.config(fg='black')
            self.btn_heater_setpoint_2.config(fg='black')
        else:
            if heater_control_effort and fan_control_effort:
                button_color = 'purple'
            elif heater_control_effort:
                button_color = 'red'
            elif fan_control_effort:
                button_color = 'blue'
            else:
                button_color = 'black'
            btn_heater_setpoint.config(fg=button_color)
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
