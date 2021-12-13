# file: res_loop_2420.py
# author: Steve Novakov 2019-06-29
# desc: JV scan using Keithley 2410 over GPIB

import visa
import nanodac
from time import sleep
import matplotlib.pyplot as pt
from datetime import datetime
import csv
import numpy as np
from scipy import polyfit, poly1d

ADDR_2410 = 25

rm = visa.ResourceManager()
k_jv = rm.open_resource('GPIB0::{}::INSTR'.format(ADDR_2410))

nanodac.NDConnect()

def WriteCommand(command):
  print(command)
  k_jv.write(command)

# SETTINGS

filestr = "Cu15_400c_5mtorr_125um_pad_1v_re"
EXTRA_BAKETIME = 60 # on top of standard 600s in nanodac methods

# resistance scan setting

V_BIAS = 1 # (V)

SN = 20
DELAY = 5
CURRENT_LIMIT = 100e-6

# temperature scan settings

START = 30
END = 200

TN = 18

# START SCAN

uptemps = np.linspace(START, END, TN)

timestamp = datetime.now().strftime("%Y-%jT%H%M%S")
filename = "../../data/" + timestamp + "_" + filestr + ".csv"

WriteCommand("*RST; :STAT:PRES; *CLS")

sleep(2.0)

WriteCommand(":SYST:BEEP:STAT OFF")

WriteCommand(":SOUR:FUNC VOLT")
WriteCommand(":SOUR:VOLT:MODE FIXED")
WriteCommand(":SENS:FUNC:CONC OFF")
WriteCommand(":SENS:FUNC \"CURR\"")
WriteCommand(":SENS:CURR:PROT {}".format(CURRENT_LIMIT))

# Up Sweep

datafile = open(filename, "a")
datafile.write("DATA\n")
datafile.close()

for t in uptemps:

  print("Temperature Setpoint: {:.2f} (C)".format(t))

  tval, terr = nanodac.SetTemperatureSync(t)

  sleep(EXTRA_BAKETIME)

  samples = []

  WriteCommand(":SOUR:VOLT:LEV {}".format(V_BIAS))
  WriteCommand(":OUTP ON")

  sleep(10.0)
  
  for s in range(0, SN):
    samples.append(float(k_jv.query(":READ?").replace("\n", "").split(",")[1]))
    sleep(DELAY)

  WriteCommand(":SOUR:VOLT:LEV {}".format(0))
  WriteCommand(":OUTP OFF")

  samples = np.array(samples)

  sval = np.mean(samples)
  serr = np.std(samples)

  row = (tval, terr, V_BIAS, sval, serr)
  print(row)

  datafile = open(filename, "a")
  datafile.write("{:.6e}, {:.6e}, {:.6e}, {:.6e}, {:.6e}\n".format(*row))
  datafile.close()

WriteCommand(":OUTP OFF")
