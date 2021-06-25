import controller
import numpy as np

keithley = controller.setup( "hlab_2110", terminal = "FRON", use_pyvisapy = True )

EXPERIMENT = '2PT_IV'
READ_INTERVAL = 0.01
CURRENT_LIMIT = 0.001
NUM_SAMPLE = 1
SOURCE_VOTLAGES = np.linspace( -1, 1, 30)
NUM_MEASUREMENT = 5

datapath = 'data'
samplename = 'test_R'

(data, header) = controller.voltage_sweep( keithley, EXPERIMENT, SOURCE_VOTLAGES, CURRENT_LIMIT, NUM_SAMPLE, READ_INTERVAL )


# EXPERIMENT = '2PT'
# READ_INTERVAL = 0.1
# NUM_SAMPLE = 5
# SOURCE_CURRENT = 0.1
# NUM_MEASUREMENT = 5

# datapath = 'data'
# samplename = 'test_R'

# (data, header) = controller.measure_resistance( keithley, EXPERIMENT, SOURCE_CURRENT, NUM_SAMPLE, READ_INTERVAL, NUM_MEASUREMENT )
# controller.save_as_csv( data, datapath, samplename, EXPERIMENT, header )