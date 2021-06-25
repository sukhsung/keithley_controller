import pyvisa as visa
import numpy as np
import time
import os

def setup( model_name, terminal = "REAR", use_pyvisapy = True ):

    if model_name == "hlab_2450":
        model = "USB0::0x05E6::0x2450::04451534::INSTR"
    elif model_name == "hlab_2110":
        model = "USB0::0x05E6::0x2110::8011648::INSTR"
    else :
        print( "Unsupported Model" )

    if ( terminal == "FRONT" ):
        terminal = "FRON"

    if ( terminal != "REAR" and terminal !="FRON" ):
        print( "Unsupported Terminal" )

    # INITIALIZE VISA
    if use_pyvisapy:
        rm = visa.ResourceManager("@py")
        print( "Using pyvisa-py backend" )
    else :
        rm = visa.ResourceManager()

    # INITIALIZING AND COMMUNICATING WITH KEITHLEY
    keithley = rm.open_resource( model )    
    keithley.write("*RST; :STAT:PRES; *CLS")
    keithley.write(":OUTPut:STATe OFF")
    keithley.write(":SYST:BEEP {},{}".format(500,0.2))
    keithley.write(":ROUT:TERM {}".format(terminal))
    print( "Using {} terminal".format(terminal) )
    

    return keithley

def list_devices( ):
    rm = visa.ResourceManager("@py")
    rm.list_resources()

def current_sweep( keithley ):

    # Setting Current Source
    keithley.write(":SOUR:FUNC: CURR")
    

def measure_resistance( keithley, FOUR_OR_TWO, source_current, NUM_SAMPLE, READ_INTERVAL, NUM_MEASUREMENT ):

    # Switch to 4-Point Measurement
    if FOUR_OR_TWO == "4PT":
        keithley.write(":SENS:VOLT:RSEN ON")
        print( "4 Point Resistance Measurement:")
        print( "FH - SH - Device - SL - FL" )
    elif FOUR_OR_TWO == "2PT":
        keithley.write(":SENS:VOLT:RSEN OFF")
        print( "2 Point Resistance Measurement:")
        print( "FH - Device - FL" )
    else:
        print( "Unsupported Mode")
        return

    ## MEASUREMENT SETUP

    # Set to source current
    keithley.write(":SOUR:FUNC CURR")
    keithley.write(":SOUR:CURR {}".format(source_current))
    print( "Sourcing Current: {}A\n".format(source_current))
    
    # Measure Resistance
    keithley.write(":SENS:FUNC \"VOLT\"")
    keithley.write(":SENS:VOLT:UNIT VOLT")
    keithley.write("SENS:VOLT:RANG:AUTO ON") #### Auto range

    # trigger for taking 3 samples per measurement with read_interveral in between to defbuffer1
    keithley.write(":TRIG:LOAD \"SimpleLoop\", {}, {}, \"defbuffer1\"".format(NUM_SAMPLE,READ_INTERVAL))

    Vs = []
    Is = []
    Ts = []
    Rs = []
    time_init = time.time()
    # Start Measuring
    header = "Time (s),Source Current (A),Measured Voltage (V),Resistance (Ohm)"
    print( "[{}]".format(header) )
    counter = 0
    while counter < NUM_MEASUREMENT:
        try:
            keithley.write("OUTP ON")
            keithley.write("INIT")
            keithley.write("*WAI")
            keithley.write("TRAC:DATA? 1, 1, \"defbuffer1\", SOUR, READ")
            keithley.write("OUTP OFF")
            curT = time.time()-time_init


            bufferdata = keithley.read()
            curI = float(bufferdata.split(",")[0] )
            curV = float(bufferdata.split(",")[1] )
            curR = curV/curI

            Is.append( curI )
            Vs.append( curV )
            Ts.append( curT )
            Rs.append( curR )
            print( [curT, curI, curV, curR] )
            counter += 1
        except KeyboardInterrupt:
            print( "KeyboardInterrupt: Ending Early")
            counter = NUM_MEASUREMENT

    data = np.array( [Ts,Is,Vs,Rs]).transpose()

    return data, header

def voltage_sweep( keithley, EXPERIMENT, SOURCE_VOTLAGES, CURRENT_LIMIT, NUM_SAMPLE, READ_INTERVAL ):

    if EXPERIMENT == "2PT_IV":
        keithley.write(":SENS:VOLT:RSEN OFF")
        print( "2 Point Voltage Sweep")
        print( "FH - Device - FL" )
    else:
        print( "Unsupported Mode")
        return

    ## MEASUREMENT SETUP

    # Set to source voltage
    keithley.write(":SOUR:FUNC VOLT")
    keithley.write(":SOUR:CURR:ILIM {}".format(CURRENT_LIMIT))
    
    # Measure Resistance
    keithley.write(":SENS:FUNC \"CURR\"")
    keithley.write(":SENS:CURR:UNIT AMP")
    keithley.write("CURR:RANG:AUTO ON") #### Auto range

    # trigger for taking 3 samples per measurement with read_interveral in between to defbuffer1
    keithley.write(":TRIG:LOAD \"SimpleLoop\", {}, {}, \"defbuffer1\"".format(NUM_SAMPLE,READ_INTERVAL))

    Vs = []
    Is = []
    Ts = []
    time_init = time.time()
    # Start Measuring
    header = "Time (s),Source Voltage (V),Measured Current (I)"
    print( "[{}]".format(header) )
    for source_v in SOURCE_VOTLAGES:
        #keithley.write(":SENS:AZER:ONCE")
        keithley.write(":SOUR:VOLT {}".format(source_v))
        keithley.write("OUTP ON")
        keithley.write("INIT")
        keithley.write("*WAI")
        keithley.write("TRAC:DATA? 1, 1, \"defbuffer1\", SOUR, READ")
        keithley.write("OUTP OFF")
        curT = time.time()-time_init

        bufferdata = keithley.read()
        curV = float(bufferdata.split(",")[0] )
        curI = float(bufferdata.split(",")[1] )

        Is.append( curI )
        Vs.append( curV )
        Ts.append( curT )
        print( [curT, curV, curI] )

    data = np.array( [Ts,Vs,Is]).transpose()

    return data, header

def save_as_csv( data, savedir, sample_name, experiment, header ):

    savepath = os.path.join( savedir, sample_name)
    if not os.path.exists( savepath ):
        os.makedirs( savepath )

    now = time.localtime()
    fname = "{}_{}".format(time.strftime("%H%M",now), experiment)
    
    fullpath = os.path.join( savepath,fname+".csv" )
    while os.path.isfile( fullpath ):
        fname = fname + "_"
        fullpath = os.path.join( savepath,fname+".csv" )

    f = open( fullpath ,'w')
    f.write("{}\n".format(header))
    np.savetxt(f, data, delimiter = ",")
    f.close()
