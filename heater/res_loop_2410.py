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

ADDR_2410 = 25

global kl2410
rm = visa.ResourceManager()
kl2410 = rm.open_resource('GPIB0::{}::INSTR'.format(ADDR_2410))

nanodac.NDConnect()

def WriteCommand(command):
  print(command)
  global kl2410
  kl2410.write(command)

def ResLoop(filestr, resrange=200):

  global kl2410
  timestamp = datetime.now().strftime("%Y-%jT%H%M%S")
  filename = "../../data/" + timestamp + "_" + filestr + ".csv"

  EXTRA_BAKETIME = 600 # on top of standard 600s in nanodac methods
  
  SN = 100
  DELAY = 10.0
  CURRENT_LIMIT = 1.0
  VOLTAGE_LIMIT = 50.0

  START = 35
  END = 125
  TN = 50

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
  WriteCommand(":OUTP ON")

  # Up Sweep

  datafile = open(filename, "a")
  datafile.write("UP\n")
  datafile.close()

  for t in uptemps:

    print("Temperature Setpoint: {:.2f} (C)".format(t))

    tval, terr = nanodac.SetTemperatureSync(t)

    sleep(EXTRA_BAKETIME)

    samples = []

    for s in range(0, SN):
      samples.append(float(kl2410.query(":READ?").replace("\n", "")))
      sleep(DELAY)

    samples = np.array(samples)

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

    samples = []

    for s in range(0, SN):
      samples.append(float(kl2410.query(":READ?").replace("\n", "")))
      sleep(DELAY)

    samples = np.array(samples)

    sval = np.mean(samples)
    serr = np.std(samples)

    row = (tval, terr, sval, serr)
    print(row)

    datafile = open(filename, "a")
    datafile.write("{:.6e}, {:.6e}, {:.6e}, {:.6e}\n".format(*row))
    datafile.close()

  WriteCommand(":OUTP OFF")

  return
