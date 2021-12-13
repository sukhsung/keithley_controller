#!/bin/python
#
# file: heater_gui.py
# desc:
# author: Steve Novakov 2018-04-24
#

from tkinter.ttk import *
import tkinter as tk
from tkinter import *

import threading
import time

import nanodac

nanodac.NDConnect()

comms_lock = threading.Lock()

class HeaterGUI:
  def __init__(self, master):

    self.master = master
    self.master.title("Whachu Know About... Thermal Cycling")
    self.menubar = tk.Menu(self.master)

    self.mainframe = tk.Frame(master=self.master)

    # Connect Nanodac and Establish Keepalive and "Connected" Text

    # Config Entry Form for New Setpoint (use set temp async)

    self.InputFrame()

    # Config Display of Setpoints

    self.SetpointFrame()

    self.master.columnconfigure(1, weight=1)
    self.master.columnconfigure(0, weight=1)

    status_thread = threading.Thread(target=self.GetSetpointTemp)
    status_thread.start()

    return

  def InputFrame(self):

    inputframe = tk.Frame(master=self.master)

    sptext = tk.Label(master=inputframe, text="New Setpoint:")
    sptext['font'] = ('Helvetica',26)
    sptext.grid(row=0, column=0, padx=10, pady=20)

    self.spfield = tk.Entry(master=inputframe, width=40)
    self.spfield.insert(0,"30.0")
    self.spfield.grid(row=1, column=0, padx=10, pady=10)

    writesp = tk.Button(inputframe, text="WRITE SETPOINT", \
      command=self.WriteSetpoint, height=3)
    writesp['font'] = ('Helvetica',30)
    writesp.grid(row=2, column=0, padx=10, pady=30)

    inputframe.grid(row=0,column=0, sticky="W")

    return

  def WriteSetpoint(self):

    newsp = float(self.spfield.get())

    if newsp > 200.0 or newsp < 30.0:
      print("Setpoint invalid. Please choose a setpoint between 30.0 and 200.0 C")
    else:
      write_thread = threading.Thread(target=self.WriteSP, args=[newsp])
      write_thread.start()
    return

  def SetpointFrame(self):

    setpointframe = tk.Frame(master=self.master)

    self.pv = tk.StringVar()
    self.tsp = tk.StringVar()
    self.wsp = tk.StringVar()

    pvlabel = tk.Label(master=setpointframe, text="PV:")
    pvlabel['font'] = ('Helvetica',26)
    pvlabel.grid(row=0, column=0, padx=10, pady=20, sticky="E")

    pvl = tk.Label(master=setpointframe, width=10, textvariable=self.pv)
    pvl['font'] = ('Helvetica',26)
    pvl.grid(row=0, column=1, padx=10, pady=20, sticky="E")

    tsplabel = tk.Label(master=setpointframe, text="Target Setpoint:")
    tsplabel['font'] = ('Helvetica',26)
    tsplabel.grid(row=1, column=0, padx=10, pady=20, sticky="E")

    tspl = tk.Label(master=setpointframe, width=10, textvariable=self.tsp)
    tspl['font'] = ('Helvetica',26)
    tspl.grid(row=1, column=1, padx=10, pady=20, sticky="E")

    wsplabel = tk.Label(master=setpointframe, text="Working Setpoint:")
    wsplabel['font'] = ('Helvetica',26)
    wsplabel.grid(row=2, column=0, padx=10, pady=10, sticky="E")

    wspl = tk.Label(master=setpointframe, width=10, textvariable=self.wsp)
    wspl['font'] = ('Helvetica',26)
    wspl.grid(row=2, column=1, padx=10, pady=20, sticky="E")

    setpointframe.grid(row=0,column=1,sticky="W")

    return

  def WriteSP(self, newsp):

    while(1):
      with comms_lock:
        nanodac.SetTemperatureAsync(newsp)
        break

    return

  def GetSetpointTemp(self):
    while(1):

      time.sleep(0.2)

      wsp = 0
      tsp = 0
      with comms_lock:

        wsp, tsp = nanodac.GetSetpoints()

        self.wsp.set(wsp)
        self.tsp.set(tsp)

        pv = nanodac.GetTemperature()

        self.pv.set(pv)

    return

if __name__ == '__main__':

  root = tk.Tk()
  heater_gui = HeaterGUI(root)
  root.mainloop()
