# file: nanopdac.py
# author: Steve Novakov 2017-06-13
# desc: library for initialization and use of Eurtotherm nanodac over
# modbus/tcp for probe station heater/chiller control.
#
# see CONNECTIVITY.txt for description of hardware connections and windows
# tcp/ip settings required for use.
#
# see simple_temp_loop.py for example usage of this library
#

import sys
import time
import numpy as np
import pymodbus
from pymodbus.client.sync import ModbusTcpClient as MTC

global client

SLEEP_TIME = 0.10 # ~10 samples/sec

def ReadRegisters(reg, cnt=1):

  while(1):

    data = []

    try:
      data = client.read_holding_registers(reg, count=cnt, unit=1)
      time.sleep(SLEEP_TIME)
      break

    except pymodbus.exceptions.ModbusIOException:
      time.sleep(SLEEP_TIME)
      continue

    except pymodbus.exceptions.ConnectionException:
      client.connect()
      time.sleep(SLEEP_TIME)
      continue

  return data

def WriteRegister(reg, value):

  while(1):

    try:
      client.write_register(reg, value, unit=1)
      time.sleep(SLEEP_TIME)
      break

    except pymodbus.exceptions.ModbusIOException:
      time.sleep(SLEEP_TIME)
      continue

    except pymodbus.exceptions.ConnectionException:
      client.connect()
      time.sleep(SLEEP_TIME)
      continue

  return

def NDConnect(ip_addr='192.168.111.222'):

  codes = {0:"Digital I/O", 1:"Non-isolated dc op", 2:"Relay op", \
    3:"TRIAC 1a1b", 4:"Relay OP", 5:"Isolated dc op (V/mA)", 6:"Digital ip",\
    7:"Isolated dc op (mA only)", 8:"Digital Op", 9:"Relay OP", 10:"Triac 2A2B"}

  ports = ["1A1B", "2A2B", "LALC", "3A3B", "LBLC", "4AC", "5AC"]

  global client
  client = MTC(ip_addr)

  if not client.connect():
    print("ERROR: NanoDAC connection failed. Exiting.")
    sys.exit(0)
  else:
    print("Connected to " + ip_addr)

  data = client.read_holding_registers(4340, count=7, unit =1)

  print("Port Configuration:")

  for i, j in zip(ports, data.registers):
    print("\t" + str(i) + " : " + codes[int(j)])

  return

def SetTemperatureAsync(temp):

  temp_str = "{:.1f}".format(float(temp))
  temp_val = int(temp_str.replace(".",""))

  ret = WriteRegister(514, temp_val)

  time.sleep(SLEEP_TIME)

  data = ReadRegisters(514, cnt=1)

  if int(data.registers[0]) == temp_val:
    print("TSP --> " + str(temp_str))
    return True

  print("ERROR: TSP not changed.\n")
  return False

def SetTemperatureSync(new_sp):

  # Poll for current temp

  old_sp = GetTemperature()
  swing = abs(new_sp - old_sp)
  stable = 0.01 * swing

  if stable < 0.325:
    stable = 0.325

  if not SetTemperatureAsync(new_sp):
    print("Setpoint Fail")
    return

  temps = np.zeros(100)

  for i in range(0, 100):
    temps[i] = GetTemperature()

  # Poll nanodac and wait for <2% stdev settling, or 0.5deg, 100 sample window

  while(1):

    temps = np.roll(temps, 1)
    temps[0] = GetTemperature()

    mean = np.mean(temps)
    std = np.std(temps)

    if (abs(mean - new_sp) < stable) and (std < stable):
      print("Setpoint Reached " + "{:.2f}".format(mean) +\
        ",{:.2f}".format(std) + ", stabilizing (600s) ...")

      break

  # Wait 600s for stability, then poll again for final statistics
  
  time.sleep(600.0)

  for i in range(0, 100):
    temps[i] = GetTemperature()

  mean = np.mean(temps)
  std = np.std(temps)

  return mean, std

def GetTemperature():

  data = ReadRegisters(512)

  tempstr = str(data.registers[0])

  temp = float(tempstr[:-1] + "." + tempstr[-1])

  return temp


def GetSetpoints():

  data = ReadRegisters(514)

  tempstr = str(data.registers[0])

  target_setpoint = float(tempstr[:-1] + "." + tempstr[-1])

  data = ReadRegisters(515)

  tempstr = str(data.registers[0])

  working_setpoint = float(tempstr[:-1] + "." + tempstr[-1])

  return target_setpoint, working_setpoint
