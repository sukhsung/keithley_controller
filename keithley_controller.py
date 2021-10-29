import pyvisa as visa
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime, timedelta
import os.path

from pyvisa.typing import VISAHandler

class controller:
    
    def __init__(self, device_address, use_pyvisapy = True, verbose = False):
        self.device_address = device_address
        self.verbose = verbose
        # INITIALIZE VISA
        if use_pyvisapy:
            self.resource_manager = visa.ResourceManager("@py")
            print( "Using pyvisa-py backend\n" )
        else :
            self.resource_manager = visa.ResourceManager()

        
        self.device = self.resource_manager.open_resource( device_address )    
        self.reset()

    def current_device(self) :
        print(self.query("*IDN?"))

    def write( self, command ):
        if self.verbose :
            print("    {}".format(command))
        self.device.write(command)

    def query( self, command, delay = None ):
        if self.verbose :
            print("    {}".format(command))
        return self.device.query(command, delay=delay)
    

    def reset( self ) :
        print( "Resetting..." )
        self.write("*RST; :STAT:PRES; *CLS")
        self.write(":OUTP OFF")
        self.write(":SYST:BEEP {},{}".format(500,0.2))
        print( "\n" )
        
    def save_as_csv( self, data, header, savedir, sample_name, experiment ):

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
        print( "Data saved as {}".format(fullpath) )


class keithley_2110( controller ):
    def __init__(self, serial_number, use_pyvisapy = True, verbose = False):
        address = "USB0::0x05E6::0x2110::{}::INSTR".format(serial_number)
        controller.__init__(self, address, use_pyvisapy, verbose)
        self.serial_number = serial_number
        self.measure_types = ["VOLT", "VOLT:DC", "VOLT:AC", "CURR", "CURR:DC", "CURR:AC", "RES", "RES_2PT", "FRES", "RES_4PT", "CAP"]

    def do_measurement( self, MEASUREMENT_TYPE, MEASUREMENT_RANGE="AUTO", NUM_POINTS=1, INTERVAL=0.1 ):
        ## Setup measurement and run repeated measurements
        header = self.setup_measurement( MEASUREMENT_TYPE, range = MEASUREMENT_RANGE )
        print( "[{}]".format(header) )
        data = self.measure( NUM_POINTS, INTERVAL )
        return data, header

    def setup_measurement( self, type, range ):
        # Set Measurement Function
        if type in self.measure_types:
            if type in ["VOLT", "VOLT:DC", "VOLT:AC"]:
                header = "Time (s),Voltage (V)"          

            elif type in ["CURR", "CURR:DC", "CURR:AC"]:
                header = "Time (s),Current (A)"        

            elif type in ["RES", "RES_2PT"]:
                header = "Time (s),Resistance (Ohm)"   
                type = "RES"
                
            elif type in ["FRES", "RES_4PT"]:
                type = "FRES"
                header = "Time (s),Resistance (Ohm)"     

            elif type == "CAP":
                header = "Time (s),Capacitance (F)"   
        else :
            print( "!!!! Illegal Measurement Type !!!!")
            return None
        
        self.write("FUNC \"{}\"".format(type))  
        # Set Measurement Range
        if range == "AUTO" :
            self.write("{}:RANG:AUTO ON".format(type))
        elif self.is_in_range( type, range ):
            self.write("{}:RANG {}").format(type, range)
        else :
            print( "!!!! Illegal Range !!!!")
            return None

        return header

    def is_in_range( self, type, range ):
        result = False
        if type == "VOLT:DC" or type == "VOLT":
            if range >= -1000 and range <= 1000:
                return True
        elif type == "VOLT:AC":
            if range >= 0 and range <= 750:
                return True
        elif type == "CURR:DC" or type == "CURR":
            if range >= -10 and range <= 10:
                return True
        elif type == "CURR:AC":
            if range >= 0 and range <= 10:
                return True
        elif type == "RES" or type == "FRES":
            if range >= 0 and range <= 100e6:
                return True
        elif type == "CAP":
            if range >= 0 and range <= 10e-3:
                return True
        return result

    def measure( self, NUM_POINTS, INTERVAL ):
        counter = 0
        TYs = []

        self.write("INIT")
        time_init = time.time()
        # Start Measuring
        while counter < NUM_POINTS:
            try:
                curT = time.time()-time_init
                curY = self.measure_once( INTERVAL )
                
                TYs.append( [curT, curY] )
                print( [curT, curY] )
                counter += 1


            except KeyboardInterrupt:
                print( "KeyboardInterrupt: Ending Early")
                counter = NUM_POINTS

        data = np.array( TYs )
        return data

    def measure_once( self, delay=None ):
        return np.float(self.query( "FETC?", delay=delay)) # Sending 'FETCh?' after 'INIT' is much faster than 'READ?'
        #return float(self.query( "READ?" ))

class keithley_2450( controller ):
    def __init__(self, serial_number, use_pyvisapy = True, verbose = False):
        address = "USB0::0x05E6::0x2450::{}::INSTR".format(serial_number)
        controller.__init__(self, address, use_pyvisapy, verbose)
        self.serial_number = serial_number


    def measure_resistance( self, FOUR_OR_TWO="2PT", NUM_POINTS=1, INTERVAL=0.1, SOURCE_CURRENT="N/A", VOLTAGE_LIMIT="N/A", SENSE_RANGE="AUTO", NUM_SAMPLES=5, NPLC=1 ):
        
        # Switch to rear terminals
        self.write(":ROUT:TERM REAR")
        print(self.query(":ROUT:TERM?\n"))
        
        # Switch to 4-Point Measurement
        if FOUR_OR_TWO == "4PT":
            print( "4 Point Resistance Measurement:")
            self.write(":SENS:VOLT:RSEN ON")
        elif FOUR_OR_TWO == "2PT":
            print( "2 Point Resistance Measurement:")
            #self.write(":SENS:VOLT:RSEN OFF")
        else:
            print( "Unsupported Mode")
            return "N/A", "N/A"

        ## MEASUREMENT SETUP
        if not self.isnumber(SOURCE_CURRENT): 
            print( "SOURCE CURRENT NOT DEFINED: ABORTING" )
            return "N/A", "N/A"

        if self.isnumber(NPLC):
            self.write("SENS:VOLT:NPLC {}".format(NPLC))

        NPLC = float(self.query("SENS:VOLT:NPLC?"))
        sample_time = NUM_SAMPLES*NPLC/(60.0) * 1.01
        if INTERVAL > sample_time:
            sample_time = INTERVAL
        print( "Sample Time: {}".format(sample_time))


        # Set to source current
        print( "Sourcing Current: {}A\n".format(SOURCE_CURRENT))
        self.write(":SOUR:FUNC CURR")
        self.write(":SOUR:CURR {}".format(SOURCE_CURRENT))

        if self.isnumber(VOLTAGE_LIMIT): 
            print( "Voltage Limit: {}V\n".format(SOURCE_CURRENT))
            self.write("SOUR:CURR:VLIM {}".format(VOLTAGE_LIMIT))

        
        # Set to measure voltage
        self.write(":SENS:FUNC \"VOLT\"")
        self.write("SENS:VOLT:RANG:AUTO ON") #### Auto range
        if SENSE_RANGE == "AUTO" :
            print("Sense Range: AUTO")
            self.write("SENS:VOLT:RANG:AUTO ON")
        else :
            print("Sense Range: VOLT".format(SENSE_RANGE))
            self.write("SENS:VOLT:RANG {}".format(SENSE_RANGE))
        print("\n")

        # trigger for taking 3 samples per measurement with read_interveral in between to defbuffer1
        self.write(":TRIG:LOAD \"SimpleLoop\", {}".format(NUM_SAMPLES))
        time_init = time.time()
        # Start Measuring
        header = "Time (s),Source Current Mean (A),Source Current Std (A),Measured Voltage Mean(V),Measured Voltage Std (V),Resistance (Ohm)"
        print( "[{}]".format(header) )
        counter = 0
        data = []
        while counter < NUM_POINTS:
            try:

                (T, Im, Is, Vm, Vs) = self.measure_once( NUM_SAMPLES, sample_time )
                dT = T-time_init
                data.append( [dT, Im, Is, Vm, Vs, Vm/Im] )
                print("[{:.3f}, {:+E}, {:+E}, {:+E}, {:+E}, {:+E}]".format(dT, Im, Is, Vm, Vs, Vm/Im))
                counter += 1
            except KeyboardInterrupt:
                print( "KeyboardInterrupt: Ending Early")
                counter = NUM_POINTS


        return data, header
        
    def measure_IV_Sweep( self, SOURCE_TYPE, SOURCE_VALUES, FOUR_OR_TWO="2PT", SOURCE_LIMIT="N/A", SENSE_RANGE="AUTO", INTERVAL=0.1, NUM_SAMPLES = 5, NPLC=1) :
        
        if SOURCE_TYPE == 'VOLT':
            SENSE_TYPE = 'CURR'
            LIMIT_TYPE = 'ILIM'
            LIMIT_UNIT = 'A'
            header = "Time (s),Voltage Mean (V),Voltage Std (V),Current Mean (A),Current Std (A)"
        elif SOURCE_TYPE == 'CURR':
            SENSE_TYPE = 'VOLT'
            LIMIT_TYPE = 'VLIM'
            LIMIT_UNIT = 'V'
            header = "Time (s),Current Mean (A),Current Std (A),Voltage Mean (V),Voltage Std (V)"
        else :
            print( "SOURCE_TYPE must be \"VOLT\" or \"CURR\"")
            return "N/A", "N/A"
        
        # Switch to rear terminals
        self.write(":ROUT:TERM REAR")
        print(self.query(":ROUT:TERM?\n"))

        # Set Voltage Source
        self.write("SOUR:FUNC {}".format(SOURCE_TYPE))
        self.write("SOUR:{}:RANG {}".format(SOURCE_TYPE, self.calculate_source_range( SOURCE_TYPE,SOURCE_VALUES)))

        if self.isnumber( SOURCE_LIMIT ):
            print( "Source Limit: {}{}\n".format(SOURCE_LIMIT, LIMIT_UNIT))
            self.write("SOUR:{}:{} {}".format(SOURCE_TYPE, LIMIT_TYPE, SOURCE_LIMIT))


        # Set Sensing
        self.write("SENS:FUNC \"{}\"".format(SENSE_TYPE))
        if SENSE_RANGE == "AUTO" :
            print("Sense Range: AUTO")
            self.write("SENS:{}:RANG:AUTO ON".format(SENSE_TYPE))
        else :
            print("Sense Range: {}".format(SENSE_RANGE))
            self.write("SENS:{}:RANG {}".format(SENSE_TYPE, SENSE_RANGE))

        # Switch 4-Point vs 2-Point Measurement
        if FOUR_OR_TWO == "4PT":
            print( "4 Point Resistance Measurement:")
            self.write(":SENS:{}:RSEN ON".format(SENSE_TYPE))
        elif FOUR_OR_TWO == "2PT":
            print( "2 Point Resistance Measurement:")
            #self.write(":SENS:{}:RSEN OFF".format(SENSE_TYPE))
        else:
            print( "Unsupported Mode")
            return "N/A", "N/A"


        if self.isnumber(NPLC):
            self.write("SENS:{}:NPLC {}".format(SENSE_TYPE, NPLC))

        NPLC = float(self.query("SENS:{}:NPLC?".format(SENSE_TYPE)))
        sample_time = NUM_SAMPLES*NPLC/(60.0) * 1.01
        if INTERVAL > sample_time:
            sample_time = INTERVAL
        print( "Sample Time: {}".format(sample_time))


        self.write(":TRIG:LOAD \"SimpleLoop\", {}".format(NUM_SAMPLES))

        data = []
        # Set Source Sweep
        print( "[{}]".format(header) )
        time_init = time.time()
        for source_value in SOURCE_VALUES:
            self.write(":SOUR:{} {}".format(SOURCE_TYPE, source_value))
            
            (T, sour_ave, sour_std, sens_ave, sens_std) = self.measure_once( NUM_SAMPLES, sample_time )
            dT = T-time_init
            data.append( [dT, sour_ave, sour_std, sens_ave, sens_std] )
            print("[{:.3f}, {:+E}, {:+E}, {:+E}, {:+E}]".format(dT, sour_ave, sour_std, sens_ave, sens_std))

        return data, header
        
    
    def measure_once( self, NUM_SAMPLES, sample_time ):
        self.write("OUTP ON")
        self.write("INIT")
        self.write("*WAI")
        TIME = time.time()

        buffer_data = (self.query( "TRAC:DATA? 1, {}, \"defbuffer1\", SOUR, READ".format(NUM_SAMPLES), delay=sample_time) ).split(',')

        sources = np.asarray( buffer_data[0::2], dtype=np.float64 )  
        senses =  np.asarray( buffer_data[1::2], dtype=np.float64 )  

        self.write("OUTP OFF")

        return TIME, np.mean(sources), np.std(sources), np.mean(senses), np.std(senses)

    
    def measure_R_cont( self, SOURCE_TYPE, SOURCE_VALUE, FOUR_OR_TWO="4PT", SOURCE_LIMIT="0.001", SENSE_RANGE="AUTO", HEATMINUTE = 1, INTERVAL = 0.01, NPLC=0.1) :
        
        if SOURCE_TYPE == 'VOLT':
            SENSE_TYPE = 'CURR'
            LIMIT_TYPE = 'ILIM'
            LIMIT_UNIT = 'A'
            header = "Time (s),Voltage Mean (V),Voltage Std (V),Current Mean (A),Current Std (A)"
        elif SOURCE_TYPE == 'CURR':
            SENSE_TYPE = 'VOLT'
            LIMIT_TYPE = 'VLIM'
            LIMIT_UNIT = 'V'
            header = "Time (s),Current Mean (A),Current Std (A),Voltage Mean (V),Voltage Std (V)"
        else :
            print( "SOURCE_TYPE must be \"VOLT\" or \"CURR\"")
            return "N/A", "N/A"

        # Switch to rear terminals
        self.write(":ROUT:TERM REAR")
        print(self.query(":ROUT:TERM?\n"))


        # Set Source
        self.write("SOUR:FUNC {}".format(SOURCE_TYPE))
        self.write("SOUR:{}:RANG {}".format(SOURCE_TYPE, self.calculate_source_range( SOURCE_TYPE,SOURCE_VALUE)))
        self.write("SOUR:{} {}".format(SOURCE_TYPE, SOURCE_VALUE))

        if self.isnumber( SOURCE_LIMIT ):
            print( "Source Limit: {}{}\n".format(SOURCE_LIMIT, LIMIT_UNIT))
            self.write("SOUR:{}:{} {}".format(SOURCE_TYPE, LIMIT_TYPE, SOURCE_LIMIT))

        # Set Sensing
        self.write("SENS:FUNC \"{}\"".format(SENSE_TYPE))
        if SENSE_RANGE == "AUTO" :
            print("Sense Range: AUTO")
            self.write("SENS:{}:RANG:AUTO ON".format(SENSE_TYPE))
        else :
            print("Sense Range: {}".format(SENSE_RANGE))
            self.write("SENS:{}:RANG {}".format(SENSE_TYPE, SENSE_RANGE))

        #self.write(":SENS:{}:RSEN ON".format(SENSE_TYPE))
        #self.write(":SENS:{}:AVER:COUNT {}".format(SENSE_TYPE, NUM_SAMPLES))
        #self.write(":SENS:{}:AVER:TCON REP; AVER ON".format(SENSE_TYPE, NUM_SAMPLES))
        #self.write(":SENS:{}:AZER ON".format(SENSE_TYPE))

        # Switch 4-Point vs 2-Point Measurement
        if FOUR_OR_TWO == "4PT":
            print( "4 Point Resistance Measurement:")
            self.write(":SENS:{}:RSEN ON".format(SENSE_TYPE))
        elif FOUR_OR_TWO == "2PT":
            print( "2 Point Resistance Measurement:")
            self.write(":SENS:{}:RSEN OFF".format(SENSE_TYPE))
        else:
            print( "Unsupported Mode")
            return "N/A", "N/A"
        if self.isnumber(NPLC):
            self.write("SENS:{}:NPLC {}".format(SENSE_TYPE, NPLC))

        NPLC = float(self.query("SENS:{}:NPLC?".format(SENSE_TYPE)))
        sample_time = NPLC/(60.0) * 1.1
        if INTERVAL > sample_time:
            sample_time = INTERVAL
        print( "Sample Time: {}".format(sample_time))

        data = []
        # Set starting time
        print( "[{}]".format(header))

        def time_elapsed(start):
            delta_t = time.time() - start
            return delta_t       

        # Start continuous sourcing
        heat_time = (timedelta(minutes=HEATMINUTE)).total_seconds()
        time_init = time.time()
        dt = time_elapsed(time_init)

        while(dt < heat_time):
            try:                
                (T, sour_ave, sour_std, sens_ave, sens_std) = self.avg_R_once(sample_time )

                dt = T-time_init 
                data.append( [dt, sour_ave, sour_std, sens_ave, sens_std] )

                print("[{:.3f}, {:+E}, {:+E}]".format(dt, sour_ave, sens_ave))

            except KeyboardInterrupt:
                print( "KeyboardInterrupt: Ending Early")
                dt = heat_time

        return data, header
     

    def avg_R_once(self, sample_time):
        self.write("TRAC:CLE")
        self.write("OUTP ON")
        self.write("INIT")
        self.write("*WAI")
        TIME = time.time()

        buffer_data = (self.query( "TRAC:DATA? 1,1, \"defbuffer1\", SOUR, READ", delay=100*sample_time) ).split(',')

        sources = np.asarray( buffer_data[0::2], dtype=np.float64)
        senses =  np.asarray( buffer_data[1::2], dtype=np.float64 )   

        self.write("OUTP OFF")

        return TIME, np.mean(sources), np.std(sources), np.mean(senses), np.mean(senses) 


    def calculate_source_range(self, type, values):
        v_ranges = [20e-3, 200e-3, 2, 20, 200]
        i_ranges = [10e-9, 100e-9, 1e-6, 10e-6, 100e-6, 1e-3, 10e-3, 100e-3, 1]

        if type == "VOLT":
            range = v_ranges
        elif type == "CURR":
            range = i_ranges
        else :
            print( "Something Wrong" )

        value = np.max(np.abs( values ))

        # find smallest range that is larger than input values
        return min(filter(lambda x: x > value, range))

    def isnumber( self, val ):
        return isinstance(val, (int, float))


class hlab_2110( keithley_2110 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2110.__init__(self, "8011648", use_pyvisapy, verbose)

class hlab_2450( keithley_2450 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2450.__init__(self, "04451534", use_pyvisapy, verbose)