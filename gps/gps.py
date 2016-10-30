import time
import datetime
from Sensor import Sensor
from my_libs import *

setup_logging()
log = logging.getLogger("GPSException")

class GPS(Sensor):
    def __init__(self):
        self.device_name = "GPS"
        self.interval = 0
        self.verbose = False

    def read(self):
        ret1 = -1
        ret2 = -1
        try:
            return 23.723493644, 90.39389374
        except:
            eprint("ERROR in READ...PI/sensors/gps/gps.py")
            log.exception('ERROR in READ...PI/sensors/gps.py')
        return ret1, ret2
        
