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
        self.serial_number = serial_number
        self.measurement_types = ["VOLT", "VOLT:DC", "VOLT:AC", "CURR", "CURR:DC", "CURR:AC", "RES", "FRES", "CAP"]

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

    def measure( self ):
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