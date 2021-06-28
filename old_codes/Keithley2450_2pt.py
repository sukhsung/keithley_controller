import pyvisa as visa
from time import sleep
import matplotlib.pyplot as pt
import numpy as np
from datetime import datetime
import csv
import os.path
import time


#filename = datetime.now().strftime("%Y-%jT%H%M%S") + "_jv2420.csv"
#filename = "data/breakdown" + "_191017_BoronN4_" + str(D) +"u_n1_" +\
            #datetime.now().strftime("%Y-%jT%H%M%S") + ".csv"
sample= "yhl-TS-PFIB-Pt_test_short2" + "_"

filename = "VI_" + sample + datetime.now().strftime("%Y-%jT%H%M%S")+".csv"
datafile = open(filename, "w", newline='')
writer = csv.writer(datafile)

pt.ion()
fig = pt.figure()
ivax = fig.add_subplot(211)
ivax.set_ylim([-1e-6, 1e-6])
ivax.set_autoscalex_on(True)
ivax.set_autoscaley_on(True)
#ivax.set_yscale('log')
ivax.grid(True, which='both')
ivax.set_ylabel(r"I (A)", fontsize=16)
ivax.xaxis.tick_top()
ivax.set_xlabel("V (V)", fontsize=16)
ivax.xaxis.set_label_position('top')
#rax = fig.add_subplot(212)
#rax.set_ylim([0, 20])
#rax.set_autoscalex_on(True)
#rax.set_autoscaley_on(True)
#rax.set_yscale('log')
#rax.grid(False)
#rax.set_ylabel(r"$R_{back}$ ($\Omega$)", fontsize=16)
#rax.set_xlabel("V (V)", fontsize=16)
fig.show()

rm = visa.ResourceManager('@py')
#rm.list_resources()
ADDR_2450 =8 #18 #7
#ADDR_2410 = 25

#VMAX = 400
#N = 121 #int(VMAX*5)
max_v = 2e-4
min_v = 0
CURRENT_LIMIT = 1e-4

READ_INTERVAL=0.02
SOAK_TIME = 0.1
N_READS = 4

current = np.empty(N_READS)

#k_back = rm.open_resource('GPIB0::{}::INSTR'.format(ADDR_2420))
#k_jv = rm.open_resource('GPIB0::{}::INSTR'.format(ADDR_2450))
k_jv = rm.open_resource('USB0::0x05E6::0x2450::04451534::INSTR')
#k_jv.timeout = 10000   #10s for timeout

def WriteCommand(instrument, command):
  print(command)
  instrument.write(command)

#WriteCommand(k_back, "*RST; :STAT:PRES; *CLS")
WriteCommand(k_jv, "*RST; :STAT:PRES; *CLS")

sleep(3.0)

#WriteCommand(k_back, ":SYST:BEEP:STAT OFF")
#WriteCommand(k_jv, ":SYST:BEEP:STAT OFF")
WriteCommand(k_jv, ":SYST:BEEP {},{}".format(500,0.2))
#WriteCommand(k_jv, ":ROUT:TERM REAR")
WriteCommand(k_jv, ":SOUR:FUNC VOLT")

#WriteCommand(k_jv, ":SOUR:VOLT:MODE FIXED")
#WriteCommand(k_jv, ":SENS:FUNC:CONC OFF")
WriteCommand(k_jv, ":SENS:FUNC \"CURR\"")
#WriteCommand(k_jv, ":SENS:CURR:PROT {}".format(CURRENT_LIMIT))
WriteCommand(k_jv, ":SOUR:VOLT:ILIMIT {}".format(CURRENT_LIMIT))
WriteCommand(k_jv, ":SENS:CURR:AZER OFF")
WriteCommand(k_jv, ":SENS:CURR:RANG:AUTO ON")


print("Starting Sweep")

N = 50
voltages = np.linspace(min_v, max_v, N)

for v in voltages:

  timeb=time.time()
  WriteCommand(k_jv, ":SENS:AZER:ONCE")
  WriteCommand(k_jv, ":SOUR:VOLT:LEV {}".format(v))
  WriteCommand(k_jv, ":SOUR:VOLT:DEL {}".format(SOAK_TIME))
  WriteCommand(k_jv, ":TRIG:LOAD \"SimpleLoop\", 3, {}, \"defbuffer1\"".format(READ_INTERVAL))
  WriteCommand(k_jv, ":OUTP ON")
  WriteCommand(k_jv, ":INIT")
  WriteCommand(k_jv, ":*WAI")
  WriteCommand(k_jv, ":TRAC:DATA? 1, 3, \"defbuffer1\", READ, TIME")
  WriteCommand(k_jv, ":OUTP OFF")
  timedif=time.time()-timeb

  mdata=k_jv.read()
  data = mdata.split(",")[::2]  #current value, [1::2] for time
  print(mdata.split(",")[1::2])
  #current[i] = float(k_jv.read())
  for i in range(0,int(len(data))):
    current[i]=float(data[i])
  writer.writerow([v, np.mean(current), np.std(current), v/(np.mean(current))])
  #writer.writerow([v, np.mean(current), np.std(current), float(mdata.split(",")[9])])
  #writer.writerow([v, np.mean(current), np.std(current),timedif, timeb])

  plotval = abs(np.mean(current)) + 1e-10
  ivax.scatter(v, plotval, color='black')

  tmp = fig.canvas.draw()
  pt.pause(0.05)

WriteCommand(k_jv, ":OUTP OFF")

k_jv.close()
datafile.close()
