import pyvisa as visa

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



class keithley_2110( controller ):
    def __init__(self, serial_number, use_pyvisapy = True, verbose = False):
        address = "USB0::0x05E6::0x2110::{}::INSTR".format(serial_number)
        controller.__init__(self, address, use_pyvisapy, verbose)
        self.serial_number = 8011648

    def measure_resistance( self, FOUR_OR_TWO, RESISTANCE_RANGE="AUTO" ):

        # Set 4-point or 2-point measurement
        if FOUR_OR_TWO == 4:
            RES = "FRES"
        elif FOUR_OR_TWO == 2:
            RES = "RES"
        self.write("FUNC \"{}\"".format(RES))

        if RESISTANCE_RANGE == "AUTO":
            self.write("{}:RANG:AUTO ON".format(RES))
        elif (RESISTANCE_RANGE >=0 and RESISTANCE_RANGE <= 100e6):
            self.write("{}:RANG {}".format(RES,RESISTANCE_RANGE))

        data = self.query( "READ?" )
        return data

    def measure_capacitance( self, CAPACITANCE_RANGE="AUTO"):
        self.write("FUNC \"CAP\"")

        if CAPACITANCE_RANGE == "AUTO":
            self.write("CAP:RANG:AUTO ON")
        elif (CAPACITANCE_RANGE >=0 and CAPACITANCE_RANGE <= 10e-3):
            self.write("CAP:RANG {}".format(CAPACITANCE_RANGE))

        data = self.query( "READ?" )
        return data

class keithley_2450( controller ):
    def __init__(self, serial_number, use_pyvisapy = True, verbose = False):
        address = "USB0::0x05E6::0x2450::{}::INSTR".format(serial_number)
        controller.__init__(self, address, use_pyvisapy, verbose)
        self.serial_number = 8011648

    def four_point_resistance( self ):
        return
    def two_point_resistance( self ):
        return

class hlab_2110( keithley_2110 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2110.__init__(self, "8011648", use_pyvisapy, verbose)

class hlab_2450( keithley_2450 ):
    def __init__(self, use_pyvisapy = True, verbose = False):
        keithley_2110.__init__(self, "04451534", use_pyvisapy, verbose)