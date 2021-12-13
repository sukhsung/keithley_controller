# file: res_temp_sweep_2420.py
# author: Pat Kezer 2021-12-13
# desc: sweep temperature while measureing resistance

import visa
import nanodac
from time import sleep
import matplotlib.pyplot as pt
from datetime import datetime
import csv
import numpy as np
from scipy import polyfit, poly1d

KEITHLEY_2420 = 25     # Keithley address


rm = visa.ResourceManager()
# connect Keithley
k_jv = rm.open_resource('GPIB0::{}::INSTR'.format(KEITHLEY_2420))

# connect temp controller
nanodac.NDConnect()


def WriteCommand(instrument, command):
  print(command)
  instrument.write(command)

# SETTINGS
EXTRA_BAKETIME = 60 # on top of standard 600s in nanodac methods


# scan settings for Keithley

ISRC =  # I(A)
SN = 20
DELAY = 5
VOLT_LIMIT = # V(V)


# temperature scan settings

START = 30 # start temp
END = 200  # end temp
TN = 100   # number of points

up_temp = np.linspace(START,END,TN)
temps = np.append(up_temp,up_temp[::-1])


filestr = ""   #input sample name/identifier
timestamp = datetime.now().strftime("%Y-%jT%H%M%S")
filename = "../../data/" + timestamp + "_" + filestr + ".csv"

datafile = open(filename, "a+", newline='')
writer = csv.writer(datafile)
writer.writerow(["Temp_set"]+["Temp"]+["ISRC"]+["Resistance"]+\
                ["Voltage"]\
                )
datafile.close()



WriteCommand(k_jv, "*RST; :STAT:PRES; *CLS")

sleep(3.0)

WriteCommand(k_jv, ":SYST:BEEP:STAT OFF")
WriteCommand(k_jv, ":SOUR:FUNC CURR")
WriteCommand(k_jv, ":SOUR:CURR:MODE FIXED")
WriteCommand(k_jv, ":SENS:FUNC:CONC OFF") 
WriteCommand(k_jv, ":SENS:FUNC \"VOLT\"")
WriteCommand(k_jv, ":SENS:VOLT:PROT {}".format(VOLT_LIMIT))
WriteCommand(k_jv, ":SYST:RSEN off")
WriteCommand(k_jv, ":SOUR:CURR:LEV 0.0") 
WriteCommand(k_jv, ":OUTP ON") 


# Temp Sweep

datafile = open(filename, "a")
datafile.write("DATA\n")
datafile.close()

for t in temps:

    print("Temperature Setpoint: {:.2f} C".format(t))

    tval, terr = nanodac.SetTemperatureSync(t)
    sleep(EXTRA_BAKETIME)

    WriteCommand(k_jv, ":SOUR:CURR:LEV {}".format(ISRC))
    WriteCommand(k_jv, ":OUTP ON")
    WriteCommand(k_jv, ":READ?")
    sleep(0.01)
    tmp_data = k_jv.read().split(",")[0]
    volt = float(tmp_data)
    res = volt/ISRC

    data_row = [ tval , terr , ISRC , res , volt ]

    writer.writerow(data_row)

    WriteCommand(k_jv, ":OUTP OFF")
    print(data_row)




WriteCommand(k_jv, ":OUTP OFF")
k_jv.close()
datafile.close()
































