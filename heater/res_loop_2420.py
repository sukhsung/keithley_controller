# file: res_loop_2420.py
# author: Steve Novakov 2017-07-31
# desc: JV scan using Keithley 2420 over GPIB

import visa
import nanodac
from time import sleep
import matplotlib.pyplot as pt
from datetime import datetime
import csv
import numpy as np
from scipy import polyfit, poly1d

global keithley

rm = visa.ResourceManager()
ADDR_2420 = 24
keithley = rm.open_resource('GPIB0::{}::INSTR'.format(ADDR_2420))
nanodac.NDConnect()

def WriteCommand(command):
  print(command)
  global keithley
  keithley.write(command)

def ResLoop(filestr, resrange=200):

  global keithley
  timestamp = datetime.now().strftime("%Y-%jT%H%M%S")
  filename = "../../data/" + timestamp + "_" + filestr + ".csv"

  EXTRA_BAKETIME = 300 # on top of standard 600s
  
  SN = 100
  DELAY = 0.5
  CURRENT_LIMIT = 1.0
  VOLTAGE_LIMIT = 50.0

  START = 40
  END = 150
  TN = 25

  uptemps = np.linspace(START, END, TN)
  downtemps = uptemps[::-1]
  downtemps = downtemps[1:]

  ###################################################################
  ##
  ## Built-in resistivity tester
  ##
  ###################################################################

  WriteCommand("*RST; :STAT:PRES; *CLS")

  sleep(2.0)

  WriteCommand(":SENS:FUNC \"RES\"")
  WriteCommand(":SENS:RES:MODE AUTO")
  WriteCommand(":RES:RANG " + str(resrange))
  WriteCommand(":SYST:RSEN OFF")
  WriteCommand(":FORM:ELEM RES")

  # Up Sweep

  datafile = open(filename, "a")
  datafile.write("UP\n")
  datafile.close()

  for t in uptemps:

    print("Temperature Setpoint: {:.2f} (C)".format(t))

    tval, terr = nanodac.SetTemperatureSync(t)

    sleep(EXTRA_BAKETIME)
    
    WriteCommand(":OUTP ON")

    samples = []

    for s in range(0, SN):
      global keithley
      samples.append(float(keithley.query(":READ?").replace("\n", "")))
      sleep(DELAY)

    samples = np.array(samples)

    WriteCommand(":OUTP OFF")

    sval = np.mean(samples)
    serr = np.std(samples)

    row = (tval, terr, sval, serr)
    print(row)

    datafile = open(filename, "a")
    datafile.write("{:.6e}, {:.6e}, {:.6e}, {:.6e}\n".format(*row))
    datafile.close()

  # Down Sweep
  datafile = open(filename, "a")
  datafile.write("DOWN\n")
  datafile.close()

  for t in downtemps:

    print("Temperature Setpoint: {:.2f} (C)".format(t))

    tval, terr = nanodac.SetTemperatureSync(t)

    sleep(EXTRA_BAKETIME)

    WriteCommand(":OUTP ON")

    samples = []

    for s in range(0, SN):
      global keithley
      samples.append(float(keithley.query(":READ?").replace("\n", "")))
      sleep(DELAY)

    samples = np.array(samples)

    WriteCommand(":OUTP OFF")

    sval = np.mean(samples)
    serr = np.std(samples)

    row = (tval, terr, sval, serr)
    print(row)

    datafile = open(filename, "a")
    datafile.write("{:.6e}, {:.6e}, {:.6e}, {:.6e}\n".format(*row))
    datafile.close()


  datafile.close()

  return
