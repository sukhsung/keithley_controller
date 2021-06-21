#
# Test script for testing 2w resistance measurement
# with Keithley 2450 over USB.
#
# Emily Rennich 2020-05-28
# Modfied by Suk Hyun Sung 2021-06-21
#

import pyvisa as visa
import time
from time import sleep
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime

rm = visa.ResourceManager('@py')

start_time = time.time()
now = datetime.now()

NS = 30
NL = 20


#INITIALIZING AND COMMUNICATING WITH KEITHLEY
# Used print(rm.list_resources()) to find device name
keithley = rm.open_resource('USB0::0x05E6::0x2450::04451534::INSTR')

print("Instruments: \n")
print(keithley.query("*IDN?"))
keithley.timeout = 2500

# Reset keithley + create new buffer
keithley.write("*RST; :STAT:PRES; *CLS")

# trigger for taking one measurement with 1/10 second delay
keithley.write("TRIG:LOAD \"SimpleLoop\", 1".format(NS))


## FOUR-POINT MEASUREMENT SETUP
# Set to source current
keithley.write(":SOUR:FUNC CURR")
# Input test current
keithley.write(":SOUR:CURR 0.0001")
# Measure voltage
keithley.write(":SENS:FUNC \"VOLT\"")
keithley.write("SENS:VOLT:RANG:AUTO ON") ####
# Set to 4 wire measure mode 
keithley.write(":SENS:VOLT:RSEN ON")
# Set the measurement unit to Ohms 
keithley.write(":SENS:VOLT:UNIT OHM")
keithley.write(":DISP:SCR SWIPE_GRAPH")
keithley.write(":SENSe:VOLTage:NPLCycles 0.01")

# Measure
sleep(0.05)

fig = plt.figure()
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
plt.subplots_adjust(hspace=.5)
xs = []
ys = []

mus = []
sts = []


def animate(i, xs, ys):

    # Gather data from the keithley
    keithley.write("OUTP ON")
    keithley.write("INIT")
    keithley.write("*WAI")
    data = keithley.query("TRAC:DATA? 1, 1, \"defbuffer1\", READ".format(NS))
    data = np.array(data.split(","), dtype="float64")
    mu, sigma = (np.mean(data), np.std(data))
    print(data)

    # Add x and y to lists
    xs.append(time.time() - start_time)
    ys.append(mu)

    mus.append(mu)
    sts.append(sigma)

    # Limit x and y lists to 20 items
    xs1 = xs[-20:]
    ys1 = ys[-20:]

    # Draw plots
    ax1.clear()
    ax1.plot(xs, ys)
    ax2.clear()
    ax2.plot(xs1, ys1)

    # Formatting
    fig.text(0.5, 0.03, 'Time (sec)', ha='center', va='center')
    fig.text(0.04, 0.5, 'Resistance (ohms)', ha='center', va='center', rotation='vertical')
    ax1.set_title('All Measurements')
    ax2.set_title('Most Recent 20 Measurements')
    
    #for label in ax1.get_xticklabels():
        #label.set_rotation(40)
        #label.set_horizontalalignment('right')
    ax1.set_xticks([])
    for label in ax2.get_xticklabels():
        label.set_rotation(40)
        label.set_horizontalalignment('right')
    plt.gcf().subplots_adjust(bottom=0.25)


ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1,)
plt.show()

# End 4-point 
keithley.write("OUTP OFF")
keithley.close()

csvdata = np.vstack((xs, mus, sts)).T
fname = "data/"+now.strftime("%H%M")+"_4point.csv"

if not os.path.exists('data'):
    os.makedirs('data')


f=open(fname.format(time = round(start_time)),'a')
f.write("Time (s),Resistance Mean (Ohm),Resistance Std (Ohm)\n")
np.savetxt(f, csvdata, delimiter = ",")