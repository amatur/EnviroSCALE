# !/usr/bin/env python
from __future__ import print_function
from bitstruct import *
import Queue

import mqtt
import cam
import os
from my_libs import eprint
from my_libs import get_timestamp
from my_libs import *
from struct import *
from socket import *
import traceback
import paho.mqtt.client as mqttc
import json
from circuits import Component, Debugger, handler, Event, Worker, task, Timer
import time
import datetime
from sensors.arduino import read_arduino


############################################################################
# Read from config #
############################################################################
try:
	with open("sensor_config.json", 'r') as f:
		c = json.load(f)
except IOError:
	print (IOError)
	print ("Error reading from config file: using default configuration")
###########################################################################


#################
# Setup Logging #
#################
setup_logging()
log = logging.getLogger("<Dispatcher>")
# logging.disable(logging.CRITICAL)          #uncomment this to disable all logging


####################
# Read from config #
####################
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    SENSE_INTERVAL = config['SENSE_INTERVAL']
    TX_MEDIUM = config['TX_MEDIUM']
    MQTT_BROKER_HOSTNAME = config['MQTT_BROKER_HOSTNAME']
    RUNTIME = config['RUNTIME']
except:
    print("Error reading from config file: using default configuration")
    SENSE_INTERVAL = 6
    TX_MEDIUM = "wlan0"  # wlan0 for WIFI, ppp0 for 3G
    MQTT_BROKER_HOSTNAME = "iot.eclipse.org"
    RUNTIME = 50

CHECK_ALIVE_INTERVAL = 30
STARTUP_INTERVAL = 4

#####################################
# Bandwidth Consumption Calculation #
#####################################
start_tx = 0
act_payload = 0


def sense_a_bundle():
    """
    Returns:
        2 bundles of sensor data as array (dictionary)
        1st one is Reading
        2nd one is Raw Sensor Data
    """
    # packed = encode_structpack(data)
    # packed2 = encode_structpack(data_raw)
    # return packed, packed2


#########################################
# Different Encoding Schemes to Compare #
#########################################
def encode_structpack(data):
    '''
    Args:
        data:
        dictionary form data array
    Returns:
        36 bytes struct.pack
    '''
    packed = pack('ifffffffff', (data["time"]), (data["ch4"]), (data["lpg"]), (data["co2"]),
                  (data["dust"]), (data["temp"]),
                  (data["humidity"]), (data["lat"]), (data["long"]), data["cng"])
    return packed


def encode_json(data):
    '''
        Args:
            data:
            dictionary form data array
        Returns:
            162 bytes labelled data : JSON
        '''
    json_str = json.dumps(data)
    # print("JSON LEN "+ str(len(json_str)))
    # print(json_str)



def struct_pack_format(NUM_DATA):
    str = ""
    str += "u4"*NUM_DATA
    str += "u16u16"*NUM_DATA
    return str

def collect_and_encode_multiple():
    mycopy = []


    count_data = 0
    while True:
        try:
            elem = CircuitsApp.readings_queue.get(block=False)
        except:
            break
        else:
            mycopy.append(elem)
            count_data = count_data + 1
    data = {}
    for i in range(0, len(mycopy)):
        data[i] = 0
        
    for i in range(0, len(mycopy)):
        data[i] = (mycopy[i].value)
    packed = pack(struct_pack_format(len(data)), *data)
    return packed


# do something with the elements

def upload_a_bundle():
    try:
        pack1  = collect_and_encode_multiple()
        b = bytearray(pack1)
        # time = bb[0]
        # ch4 = bb[1]
        # lpg = bb[2]
        # co2 = bb[3]
        # dust = bb[4]
        # temp = bb[5]
        # humidity = bb[6]
        # lat = bb[7]
        # long = bb[8]
        # cng = bb[9]

        if (mqtt.publish_packet(b) == False):
            # traceback.print_exc()
            bb = (unpack('ifffffffff', pack1))
            strnew = "missing\t"
            for i in range(0, 10):
                strnew = strnew + str(bb[i]) + "\t"
            log.log(45, strnew)
    except:
        traceback.print_exc()
        print(EventReport("Error", time.time(), "upload_a_bundle failed."))

###############################
# statistics &OS command codes #
###############################
def get_tx_bytes():
    try:
        astring = 'cat /sys/class/net/' + TX_MEDIUM + '/statistics/tx_bytes'
        return long(os.popen(astring).read())
    except:
        return 0


def reconnect(tx=TX_MEDIUM):
    cmd = 'sudo bash netpi/restart_net.sh ' + str(tx)
    os.system(cmd)


def do_power_off():
    astring = 'sudo poweroff'
    return long(os.popen(astring).read())


def calculate_payload(given_str):
    '''
    Args:        given list
    Returns:     from given list -> estimate bytes
    '''
    return len(str(given_str).encode('utf-8'))


def time_of_now():
    return datetime.datetime.fromtimestamp(time.time()-CircuitsApp.starttime).strftime('%H:%M:%S')


"""
Main Program
"""


def blocking_sense():
    # print(time_of_now(), "blocking sensing start")
    ### we can put any blocking codes here
    # print("blocking sense done")
    return 0


class SensorHandler(Component):
    _worker = Worker(process=True)
    period = 0

    def set_period(self, period):
        self.period = period

    def ready(self, *args):
        Timer(2, go(), persist=True).register(self)

    def __repr__(self):
        return 'SensorHandler::%s' % "si"

    @handler("sense_event", priority=20)
    def sense_event(self, event):
        print(event)
        ### Fire and Wait for: task()
        # yield self.call(task(blocking_sense), self._worker)
        ### This will only print after task() is complete.
        '''
        if self.sensor.flag:
            self.sensor.flag = False
            print ('Time %f :: sensor %s reading completed' % (time_of_now(), self))
            Timer(self.sensor.period, Event.create("sense_event"), persist=False).register(self)
            # sim.add_event(sim.simclock + self.period, self)
        else:
            self.sensor.flag = True
            #sim.read_queue = sim.read_queue + self.size
            #reading = Reading(self.name, sim.simclock, self.size)
            #sim.readings_queue.put(reading)
            print ('Time %f reading sensor %s current queue %d' % (time_of_now(), self, CircuitsApp.read_queue))
            Timer(self.sensor.readlatency, Event.create("sense_event"), persist=False).register(self)
            # sim.add_event(sim.simclock + self.readlatency, self)
        print(time_of_now(), "SENSING done. Now uploading...")
        '''
        #self.fire(Event.create("upload_event"))
        print ("sense ev called")
       # Timer(CircuitsApp.sensors[0].readlatency, Event.create("upload_event"), persist=False).register(self)



class Sensor:
    def __init__(self, name="NULL", readlatency=5, period=10, size=0, gamma=0, analogpin=0):
        """
        Construct a new 'Sensor' object.
        :param name: The name of Sensor
        :param readlatency: read latency
        :param period: The period to read
        :param size: The size of sensor reading in bytes
        :return: returns nothing
        """
        self.name = name
        self.readlatency = readlatency
        self.period = period
        self.size = size
        self.gamma = gamma
        self.analogpin = analogpin

    def __repr__(self):
        return 'Sensor::%s' % self.name

    def set_period(self, period):
        self.period = period


class EventReport:
    def __init__(self, name, time, msg):
        self.name = name
        self.time = time
        self.msg = msg

    def __repr__(self):
        return ('%s \t %-14s \t %s') % (self.get_time_str(self.time), self.name, self.msg)

    def get_time_str(self, a_time):
        return datetime.datetime.fromtimestamp(a_time).strftime('%H:%M:%S')


class Reading:
    def __init__(self, sensing_time, sensor_name, size, value):
        self.sensing_time = sensing_time
        self.sensor_name = sensor_name
        self.size = size
        self.value = value

    def __repr__(self):
        return 'Reading (%s, Time::%s, Size::%f, Value:: %f)' % (self.sensor_name, str(self.sensing_time), self.size, self.value)


class SenseEvent(Event):
    """sense"""
class ReadEvent(Event):
    """read"""
class UploadEvent(Event):
    """upload"""


class UploadHandler(Component):
    _worker = Worker(process=True)

    @handler("UploadEvent", priority=120)
    def upload_event(self, event):
        ustart = time_of_now()
        print(EventReport("UploadEvent", time.time(), "started"))
        yield self.call(task(upload_a_bundle), self._worker)
        ###log.log(45, "Before upload BYTES\t" + str(get_tx_bytes()))
        # yield self.call(task(upload_a_packet), self._worker)
        ###log.log(45, "After upload BYTES\t" + str(get_tx_bytes()))
        print(EventReport("UploadEvent", time.time(), "ENDED (started at " + str(ustart) + ")"))
        CircuitsApp.timers["upload"] = Timer(c["interval"]["upload"], UploadEvent(), persist=False).register(self)


class ReadHandler(Component):
    def read_and_queue(self, sensor):
        value = read_arduino(sensor.analogpin)
        reading = Reading(time.time(), sensor.name, sensor.size, value)
        #print (reading)
        CircuitsApp.readings_queue.put(reading)
        #queue_print(CircuitsApp.readings_queue)
        print (CircuitsApp.readings_queue.qsize())


    @handler("ReadEvent", priority=20)
    def read_event(self, *args, **kwargs):
        starttime = time.time()
        #print (time_of_now(), " :: ", args, kwargs)
        print(EventReport("ReadEvent", time.time(), "started"))
        yield self.read_and_queue(args[0])
        endtime = time.time()

        #print (endtime-starttime)

def queue_print(q):
    mycopy = []
    while True:
        try:
            elem = q.get(block=False)
        except:
            break
        else:
            mycopy.append(elem)
    for elem in mycopy:
        q.put(elem)
    for elem in mycopy:
        print (elem)

class SenseHandler(Component):
    _worker = Worker(process=True)
    @handler("SenseEvent", priority=100)
    def sense_event(self, *args, **kwargs):
        "hello, I got an event"
        print (EventReport("SenseEvent", time.time(), (str(args) + ", " + str(kwargs))))
        CircuitsApp.timers["sense"] = Timer(args[0].period, SenseEvent(args[0]),  persist=False).register(self)
        self.fire(ReadEvent(args[0]))

        #yield self.fire(ReadEvent(args[0]))


class App(Component):
    h1 = SenseHandler()
    h2 = UploadHandler()
    h3 = ReadHandler()

    # reconnect(TX_MEDIUM)
    sensors = []
    readings_queue = Queue.Queue()
    read_queue = 0
    starttime = time.time()
    endtime = 0
    timers = {}

    log.info("*****   RUN START   *****")

    def set_endtime(self, time):
        self.endtime = time

    def init_scene(self):
        print ("init scene")
        self.sensors = []
        num_sensors = len(c["sensors"])
        for i in range(0, num_sensors):
            s1 = Sensor(c["sensors"][i]["name"], c["sensors"][i]["readlatency"], c["sensors"][i]["period"],
                               c["sensors"][i]["size"], c["sensors"][i]["gamma"], c["sensors"][i]["analogpin"])
            self.sensors.append(s1)

        self.set_endtime(c["interval"]["M"])
        self.bought_data = c["params"]["D"]

        rate = 1.0 * self.bought_data / c["interval"]["M"]

        print (self.sensors )

        for i in range(0, num_sensors):
            s1 = self.sensors[i]
            CircuitsApp.timers["sense"] = Timer(s1.period, SenseEvent(s1), persist=False).register(self)
            #Timer(s1.period, SenseEvent(s1, name=s1.name, period=s1.period, pin=s1.analogpin), persist=False).register(self)

        CircuitsApp.timers["upload"] = Timer( c["interval"]["upload"], UploadEvent(), persist=False).register(self)
        # u = Uploader(upload_interval, 100, rate, 3600, 10)
        # f = FailureHandler(u)

        # period_update_interval = 30
        # p = PeriodUpdater(self.sensors, period_update_interval, u)

        # rate_update_interval = 200
        # r = RateUpdater(rate_update_interval, u)

       # for s in self.sensors:
       #     self.add_event(0, s)

        # self.add_event(0, u)
        # self.add_event(0, f)
        # self.add_event(0, p)
        # self.add_event(200, r)


    '''
    @handler("exit_event", priority=20)
    def exit_event(self):
        log.info("*****   EXIT command received   *****")
        print(time_of_now(), "Exiting...")
        # print(get_tx_bytes())
        # log.log(45, "END_BYTES\t" + str(get_tx_bytes()))
        CircuitsApp.timer.persist = False
        # do_power_off()
    '''


    def started(self, component):
        while True:
            try:
                actuatorClient = mqttc.Client()
                actuatorClient.on_connect = on_connect
                actuatorClient.on_message = on_message
                actuatorClient.connect(MQTT_BROKER_HOSTNAME, 1883, 60)
                actuatorClient.loop_start()
                print(time_of_now(), "Started => Running")
                print(get_tx_bytes())
                log.log(45, "START_BYTES\t" + str(get_tx_bytes()))
                #self.fire(Event.create("sense_event"))
                #self.timer = Timer(SENSE_INTERVAL, Event.create("sense_event"), persist=True).register(self)
                #Timer(RUNTIME, Event.create("exit_event"), persist=False).register(self)
                break
            except gaierror:
                log.error("Failure connecting to MQTT controller")
                print("FAILED")
                # reconnect(TX_MEDIUM)
            time.sleep(10)
        self.init_scene()



def on_connect(client, userdata, flags, rc):
    print("PI is listening for controls from paho/test/iotBUET/piCONTROL/ with result code " + str(rc))
    client.subscribe("paho/test/iotBUET/piCONTROL/")


def on_message(client, userdata, msg):
    print("Received a control string")
    try:
        parsed_json = json.loads(msg.payload)
        if (parsed_json["power_off"] == "Y"):
            # do_power_off()
            print("Received Control: PAUSE EXECUTION")
            log.log(45, "POWEROFF BYTES\t" + str(get_tx_bytes()))
            #CircuitsApp.timers["sense"].persist = False
           # CircuitsApp.timers["sense"].reset(1000)
           # CircuitsApp.timers["upload"].reset(1000)
            CircuitsApp.h1.unregister()
            CircuitsApp.h2.unregister()
            CircuitsApp.h3.unregister()
            CircuitsApp.unregister()
            log.info("Received Control: PAUSE EXECUTION")

        if (parsed_json["power_off"] == "R"):
            # do_power_off()
            log.info("Received Control: RESET TIMER")
            CircuitsApp.timer.reset(int(parsed_json["sampling_rate"]))
            log.log(45, "RESET\t" + str(get_tx_bytes()))
            CircuitsApp.timer = Timer(SENSE_INTERVAL, Event.create("sense_event"), persist=True).register(CircuitsApp)

        if (parsed_json["camera"] == "Y"):
            print("Taking picture")
            newstr = "image" + str(get_timestamp()) + ".jpg"
            try:
                cam.take_picture(newstr)
                log.info("Successfully captured picture\t" + str(newstr))
            except:
                log.error("Error in taking picture.")
        '''

        if (parsed_json["sampling_rate"] != SENSE_INTERVAL):
            CircuitsApp.timer.reset(int(parsed_json["sampling_rate"]))
            log.info("Timer Reset. New sampling rate is\t" + str(parsed_json["sampling_rate"]))
            print("Timer resetted")
        log.info("Received external control command.")
        '''
        print("Received a control string")
        print(parsed_json)
    except:
        print("From topic: " + msg.topic + " INVALID DATA")


CircuitsApp = App()
CircuitsApp.run()
if __name__ == '__main__':
    (App() + Debugger()).run()
    log.info("Keyboard Exit.")
