import pyvisa as visa
import numpy as np
import time
import os.path

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
        print(self.device.query("*IDN?"))

    def write( self, command ):
        if self.verbose :
            print("    {}".format(command))
        self.device.write(command)

    def query( self, command ):
        if self.verbose :
            print("    {}".format(command))
        return self.device.query(command)
    

    def reset( self ) :
        print( "Resetting..." )
        self.write("*RST; :STAT:PRES; *CLS")
        self.write(":OUTP OFF")
        self.write(":OUTP:STAT OFF")
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
        self.measurement_types = ["VOLT", "VOLT:DC", "VOLT:AC", "CURR", "CURR:DC", "CURR:AC", "RES", "FRES", "CAP"]

    def measurement_resistance( self, FOUR_OR_TWO="2PT", RESISTANCE_RANGE='AUTO', NUM_POINTS=1, INTERVAL=0.1 ):
        # Set Measurement Function
        if FOUR_OR_TWO == "4PT" :
            self.setup_measurement( "FRES", range = RESISTANCE_RANGE )
        elif FOUR_OR_TWO == "2PT":
            self.setup_measurement( "RES", range = RESISTANCE_RANGE )
        else :
            print( "!!!! Illegal Resistance Measurement Type !!!!")
            return

        # Start Measuring
        header = "Time (s),Resistance (Ohm)"
        print( "[{}]".format(header) )

        data = self.measure( NUM_POINTS, INTERVAL )
        return data, header

    def measurement_voltage( self, AC_OR_DC="DC", VOLTAGE_RANGE="AUTO", NUM_POINTS=1, INTERVAL=0.1 ):
        # Set Measurement Function
        if AC_OR_DC == "DC":
            self.setup_measurement( "VOLT:DC", range = VOLTAGE_RANGE )
        elif AC_OR_DC == "AC" :
            self.setup_measurement( "VOLT:AC", range = VOLTAGE_RANGE )
        else :
            print( "!!!! Illegal Resistance Measurement Type !!!!")
            return

        # Start Measuring
        header = "Time (s),Voltage (V)"
        print( "[{}]".format(header) )

        data = self.measure( NUM_POINTS, INTERVAL )
        return data, header

    def measurement_current( self, AC_OR_DC="DC", CURRENT_RANGE="AUTO", NUM_POINTS=1, INTERVAL=0.1 ):
        # Set Measurement Function
        if AC_OR_DC == "DC":
            self.setup_measurement( "VOLT:DC", range = CURRENT_RANGE )
        elif AC_OR_DC == "AC" :
            self.setup_measurement( "VOLT:AC", range = CURRENT_RANGE )
        else :
            print( "!!!! Illegal Resistance Measurement Type !!!!")
            return

        # Start Measuring
        header = "Time (s),Current (A)"
        print( "[{}]".format(header) )

        data = self.measure( NUM_POINTS, INTERVAL )
        return data, header

    def measurment_capacitance( self, CAPACITANCE_RANGE='AUTO', NUM_POINTS=1, INTERVAL=0.1 ):
        # Set Measurement Function
        self.setup_measurement( "CAP", range = CAPACITANCE_RANGE )

        # Start Measuring
        header = "Time (s),Capacitance (F)"
        print( "[{}]".format(header) )

        data = self.measure( NUM_POINTS, INTERVAL )
        return data, header

    def setup_measurement( self, type, range ):
        # Set Measurement Function
        if type in self.measurement_types:
            self.write("FUNC \"{}\"".format(type))
        else :
            print( "!!!! Illegal Measurement Type !!!!")
            return
        
        # Set Measurement Range
        if range == "AUTO" :
            self.write("{}:RANG:AUTO ON".format(type))
        elif self.is_in_range( type, range ):
            self.write("{}:RANG {}").format(type, range)
        else :
            print( "!!!! Illegal Range !!!!")
            return

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
        Ys = []
        Ts = []
        time_init = time.time()
        # Start Measuring
        while counter < NUM_POINTS:
            try:
                curT = time.time()-time_init
                curY = self.measure()
                
                Ts.append( curT )
                Ys.append( curY )
                print( [curT, curY] )
                counter += 1
                time.sleep( INTERVAL )
            except KeyboardInterrupt:
                print( "KeyboardInterrupt: Ending Early")
                counter = NUM_POINTS

        data = np.array( [Ts,Ys]).transpose()
        return data

    def measure_once( self ):
        data = self.query( "READ?" )
        return data




class keithley_2450( controller ):
    def __init__(self, serial_number, use_pyvisapy = True, verbose = False):
        address = "USB0::0x05E6::0x2450::{}::INSTR".format(serial_number)
        controller.__init__(self, address, use_pyvisapy, verbose)
        self.serial_number = 8011648


    def measure_resistance( self, FOUR_OR_TWO="2PT", NUM_POINTS=1, INTERVAL=0.1, 
                            SOURCE_CURRENT="N/A", VOLTAGE_LIMIT="N/A", NUM_SAMPLE=3 ):

        # Switch to 4-Point Measurement
        if FOUR_OR_TWO == "4PT":
            self.write(":SENS:VOLT:RSEN ON")
            print( "4 Point Resistance Measurement:")
        elif FOUR_OR_TWO == "2PT":
            self.write(":SENS:VOLT:RSEN OFF")
            print( "2 Point Resistance Measurement:")
        else:
            print( "Unsupported Mode")
            return

        ## MEASUREMENT SETUP
        if isinstance(SOURCE_CURRENT, (int, float)): 
            print( "SOURCE CURRENT NOT DEFINED: ABORTING" )
            return

        # Set to source current
        self.write(":SOUR:FUNC CURR")
        self.write(":SOUR:CURR {}".format(SOURCE_CURRENT))
        print( "Sourcing Current: {}A\n".format(SOURCE_CURRENT))
        if isinstance(VOLTAGE_LIMIT, (int, float)): 
            self.write("SOUR:CURR:VLIM {}".format(VOLTAGE_LIMIT))
        
        # Set to measure voltage
        self.write(":SENS:FUNC \"VOLT\"")
        self.write("SENS:VOLT:RANG:AUTO ON") #### Auto range

        # trigger for taking 3 samples per measurement with read_interveral in between to defbuffer1
        self.write(":TRIG:LOAD \"SimpleLoop\", {}, {}, \"defbuffer1\"".format(NUM_SAMPLE, INTERVAL))

        Vs = []
        Is = []
        Ts = []
        Rs = []
        time_init = time.time()
        # Start Measuring
        header = "Time (s),Source Current (A),Measured Voltage (V),Resistance (Ohm)"
        print( "[{}]".format(header) )
        counter = 0
        while counter < NUM_POINTS:
            try:
                self.write("OUTP ON")
                self.write("INIT")
                self.write("*WAI")
                self.write("TRAC:DATA? 1, 1, \"defbuffer1\", SOUR, READ")
                self.write("OUTP OFF")
                curT = time.time()-time_init


                bufferdata = self.read()
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
                counter = NUM_POINTS

        data = np.array( [Ts,Is,Vs,Rs]).transpose()
        return data, header

    def measure_voltage_sweep(self, CURRENT_LIMIT, V_START, V_END, NUM_POINTS, INTERVAL):
        
        # Set Voltage Source
        self.write("SOUR:FUNC VOLT")
        self.write("SOUR:VOLT:RANG {}".format(self.calculate_source_range("VOLT",[V_START,V_END])))
        self.write("SOUR:VOLT:ILIM {}".format(CURRENT_LIMIT))

        # Set Current Sensing
        self.write("SENS:FUNC \"CURR\"")
        self.write("SENS:CURR:RANG:AUTO ON")

        # Set Linear Source Sweep
        self.write("SOUR:SWE:VOLT:LIN {}, {}, {}, {}".format(V_START, V_END, NUM_POINTS, INTERVAL))
        self.write("INIT")
        self.write("*WAI")
        self.write("TRAC:DATA? 1, {}, \"defbuffer1\", SOUR, READ".format( NUM_POINTS) )


    def measure_current_sweep(self, VOLTAGE_LIMIT, I_START, I_END, NUM_POINTS, INTERVAL):
        
        # Set Current Source
        self.write("SOUR:FUNC CURR")
        self.write("SOUR:CURR:RANG {}".format(self.calculate_source_range("CURR",[I_START,I_END])))
        self.write("SOUR:CURR:ILIM {}".format(VOLTAGE_LIMIT))

        # Set Voltage Sensing
        self.write("SENS:FUNC \"VOLT\"")
        self.write("SENS:VOLT:RANG:AUTO ON")

        # Set Linear Source Sweep
        self.write("SOUR:SWE:CURR:LIN {}, {}, {}, {}".format(I_START, I_END, NUM_POINTS, INTERVAL))
        self.write("INIT")
        self.write("*WAI")
        self.write("TRAC:DATA? 1, {}, \"defbuffer1\", SOUR, READ".format( NUM_POINTS) )

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




class hlab_2110( keithley_2110 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2110.__init__(self, "8011648", use_pyvisapy, verbose)

class hlab_2450( keithley_2450 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2110.__init__(self, "04451534", use_pyvisapy, verbose)