# !/usr/bin/env python
from __future__ import print_function
import gps.gpsdaemon
import traceback
import Queue
import paho.mqtt.client as mqttc
import paho.mqtt.publish as pub
from socket import *
from circuits import Component, Debugger, handler, Event, Worker, task, Timer
import time
import datetime

# self-written library
from functions import *
from arduino import read_arduino

from bitstruct import *
import json

# Read from config
# ------------------
'''
# size : how many bits
# id : index of event in json
# s : signed int
# u : unsigned int
# f : float
'''
d = {
    "event":
        [
            {"name": "temperature",
             "size": 10,
             "dtype": 's',
             "sensor": "dht11"
             },

            {"name": "humidity",
             "size": 8,
             "dtype": 'u',
             "sensor": "dht11"
             },

            {"name": "methane",
             "size": 10,
             "dtype": 'u',
             "sensor": "mq4"
             },

            {"name": "lpg",
             "size": 10,
             "dtype": 'u',
             "sensor": "mq6"

             },

            {"name": "co2",
             "size": 10,
             "dtype": 'u',
             "sensor": "mq135"
             },

            {"name": "dust",
             "size": 10,
             "dtype": 'u',
             "sensor": "dust"
             }
        ],
    "sensor": [
        {
            "name": "dht11",
            "readlatency": 0.6,
            "period": 8.0,
            "pin": 1
        },
        {
            "name": "mq4",
            "readlatency": 0.6,
            "period": 4.0,
            "pin": 6,
            "calib": 2
        },
        {
            "name": "mq6",
            "readlatency": 0.6,
            "period": 4.0,
            "pin": 7,
            "calib": 3
        },
        {
            "name": "mq135",
            "readlatency": 0.6,
            "period": 4.0,
            "pin": 8,
            "calib": 4
        },
        {
            "name": "dust",
            "readlatency": 0.6,
            "period": 10.0,
            "pin": 5
        }
    ],
    "params": {
        "alpha": 800,
        "beta": 1,
        "lambda": 0.005,
        "D": 100000
    },
    "interval": {
        "period_update": 100,
        "M": 1000,
        "upload": 8
    },
    "tx_medium": "wlan0",
    "mqtt_broker_host": "iqueue.ics.uci.edu"
}

sensor_conf = json.dumps(d)
c = json.loads(sensor_conf)

map_event_to_id = {}
for i in range(len(c["event"])):
    map_event_to_id[c["event"][i]["name"]] = i

print (map_event_to_id)

TX_MEDIUM = c['tx_medium']
MQTT_BROKER_HOSTNAME = c["mqtt_broker_host"]

HOST_ECLIPSE = "iot.eclipse.org"
HOST_IQUEUE = "iqueue.ics.uci.edu"

TIMEOUT_MQTT_RETRY = 10


# Setup Logging
# ---------------
setup_logging()
log = logging.getLogger("<Dispatcher>")
#logging.disable(logging.CRITICAL)  # uncomment this to disable all logging
logging.disable(logging.INFO)

# Queue Related
# --------------

def queue_print(q):
    print("Printing start.")
    queue_copy = []
    while True:
        try:
            elem = q.get(block=False)
        except:
            break
        else:
            queue_copy.append(elem)
    for elem in queue_copy:
        q.put(elem)
    for elem in queue_copy:
        print(elem)
    print
    "Printing end."


#need to be updated to decode geotag
def decode_bitstruct(packed_bytes, c):

    fmt_decode = "=u8"    # how many readings ahead 8 bits unsigned, initial timestamp 32 bits float
    N = unpack(fmt_decode, packed_bytes)[0]
    print("IDDD", N)
    fmt_decode += "u32"
    # initial_time = unpack(fmt_decode, packed_bytes)[1]

    # each id is 4 bits
    for i in range(N):
        fmt_decode += "u4"

    unpacked2 = unpack(fmt_decode, packed_bytes)

    list_of_sensor_ids = unpacked2[2:(2+N+1)]
    #list_of_offsets = unpacked2[(2+N):]

    for i in list_of_sensor_ids:
        fmt_decode += str(c["event"][i]["dtype"]) + str(c["event"][i]["size"])
    for i in range(N):
        fmt_decode += "u16"

    unpacked3 = unpack(fmt_decode, packed_bytes)
    return unpacked3


def extract_queue_and_encode(q):
    # Part 1: Extracting all elements from queue to "queue_copy"
    if q.empty():
        return None
    print(EventReport("Info", "Size to be uploaded: "+str(q.qsize())))
    queue_copy = []
    i = 0
    while True:
        try:
            elem = q.get(block=False)
        except:
            break
        else:
            queue_copy.append(elem)
            print(elem)
        i = i + 1
        # to put a boundary on how many elements to pop
        # if i == 8:
        #    break

    # Part 2: Encoding elements in "queue_copy" and return a python "struct" object
    N = len(queue_copy)
    data = []

    fmt_string = "=u8"  # number of readings bundled together is assumed to be in range 0-255, hence 8 bits
    data.append(N)

    fmt_string += "u32"  # initial timestamp
    data.append(queue_copy[0][2])

    # append the event ids
    for queue_elem in queue_copy:
        fmt_string += "u4"  # we have provision for maximum 16 sensors, hence 4 bits
        event_id = queue_elem[0]
        data.append(event_id)

    # append the sensor values
    for queue_elem in queue_copy:
        id = queue_elem[0]
        fmt_string += str(c["event"][id]["dtype"]) + str(c["event"][id]["size"])
        data.append(queue_elem[1])

    # append the timestamp offsets
    for queue_elem in queue_copy:
        id = queue_elem[0]
        time_actual = queue_elem[2]
        time_offset = int((time_actual - queue_copy[0][2]))
        # print(time_actual - queue_copy[0][2])
        # print(time_offset)
        fmt_string += "u16"
        data.append(time_offset)
    
    for queue_elem in queue_copy:
        fmt_string += "f32f32f32"
        data.append(queue_elem[3])
        data.append(queue_elem[4])
        data.append(queue_elem[5])    
    packed = pack(fmt_string, *data)
    #unpacked = decode_bitstruct(packed, c)
    #print("PACCCCCCCCCCC", unpacked)
    return packed


# Uploading Functions
# ---------------------

def upload_a_bundle(readings_queue):
    try:
        packed = extract_queue_and_encode(readings_queue)
        if packed==None:
            print(EventReport("Error", "Bundle not ready yet"))
            return

        if (publish_packet_raw(bytearray(packed)) == False):
            traceback.print_exc()
            newFileBytes = bytearray(packed)
            # make file
            with open('missing.bin', 'a') as newFile:
                newFile.write(newFileBytes)
                newFile.write("\n")
            print(EventReport("Missing", "publish failure recorded."))
    except:
        traceback.print_exc()
        print(EventReport("Error", "upload_a_bundle failed."))


def publish_packet_raw(message):
    try:
        msgs = [{'topic': "paho2/test/iotBUET/bulk_raw/", 'payload': message},
                ("paho/test/multiple", "multiple 2", 0, False)]
        pub.multiple(msgs, hostname=MQTT_BROKER_HOSTNAME)
        return True

    except gaierror:
        print(EventReport("Error", "MQTT publish failed."))
        return False


# Classes
# -------

class EventReport:
    def __init__(self, name, msg):
        self.name = name
        self.time = (time.time())
        self.msg = msg
        if self.name == "Error":
            log.error(self.msg)
        elif self.name == "Info":
            log.info(self.msg)
        elif self.name == "Tx":
            log.log(45, self.msg)

    def __repr__(self):
        return ('%s \t %-14s \t %s') % (self.get_time_str(self.time), self.name, self.msg)

    def get_time_str(self, a_time):
        return datetime.datetime.fromtimestamp(a_time).strftime('%H:%M:%S')

class Sensor:
    def __init__(self, index, name, readlatency, period, pin):
        self.id = index
        self.name = name
        self.readlatency = readlatency
        self.period = period
        self.pin = pin

    def __repr__(self):
        return 'Sensor::%s' % self.name

    def set_period(self, period):
        self.period = period


class Reading:
    def __init__(self, event_id, value, time):
        self.time = time
        self.value = value
        self.event_id = event_id

    def __repr__(self):
        return 'Reading (%s, Time::%s, Value:: %f)' % (
             c["event"][self.event_id]["name"], str(get_time_as_string(self.time)), self.value)

        #return str(self.event_id)
    def tuple(self):
	lat, lon, alt = gps.gpsdaemon.read()
        return (self.event_id, self.value, int(self.time), lat, lon, alt)


# Events
# -------
class SenseEvent(Event):
    """sense"""


class ReadEvent(Event):
    """read"""


class UploadEvent(Event):
    """upload"""


class UploadHandler(Component):
    _worker = Worker(process=True)

    @handler("UploadEvent", priority=120)
    def upload_event(self, *args, **kwargs):
        ustart = get_time_as_string(time.time())
        print(EventReport("UploadEvent", "started"))
        #yield self.call(task(upload_a_bundle), self._worker)
        upload_a_bundle(args[0])
        print(EventReport("UploadEvent", "ENDED (started at " + str(ustart) + ")"))
        CircuitsApp.timers["upload"] = Timer(c["interval"]["upload"], UploadEvent(args[0]), persist=False).register(self)


class ReadHandler(Component):
    def read_and_queue(self, sensor, readings_queue):
        value = read_arduino(sensor.pin)
        time_of_read = (time.time())
        sensor_name = c["sensor"][sensor.id]["name"]

        if sensor_name == "dht11":
            reading = Reading(map_event_to_id["temperature"], value[0], time_of_read)
            readings_queue.put(reading.tuple())
            reading = Reading(map_event_to_id["humidity"], value[1], time_of_read)
            readings_queue.put(reading.tuple())
        else:
            sensor_to_event = {"mq4": "methane", "mq6": "lpg", "mq135": "co2", "dust": "dust"}
            reading = Reading(map_event_to_id[sensor_to_event[sensor_name]], value, time_of_read)
            readings_queue.put(reading.tuple())
       	    if sensor_name == "dust":
	        print ("DUSTTTT", reading)
	print (reading)




        print(readings_queue.qsize())

    @handler("ReadEvent", priority=20)
    def read_event(self, *args, **kwargs):
        starttime = time.time()
        # print (time_of_now(), " :: ", args, kwargs)
        print(EventReport("ReadEvent", "started"))
        yield self.read_and_queue(args[0], args[1])
        endtime = time.time()

        # print (endtime-starttime)


class SenseHandler(Component):
    _worker = Worker(process=True)

    @handler("SenseEvent", priority=100)
    def sense_event(self, *args, **kwargs):
        "hello, I got an event"
        print(EventReport("SenseEvent", (str(args) + ", " + str(kwargs))))
        CircuitsApp.timers["sense"] = Timer(args[0].period, SenseEvent(args[0], args[1]), persist=False).register(self)
        self.fire(ReadEvent(args[0], args[1]))

        # yield self.fire(ReadEvent(args[0]))


class App(Component):
    h1 = SenseHandler()
    h2 = UploadHandler()
    h3 = ReadHandler()

    readings_queue = Queue.Queue()

    sensors = []
    read_queue = 0
    starttime = time.time()
    print(EventReport("Info", "Start Time is: " + get_time_as_string(starttime)))

    endtime = 0
    timers = {}

    def set_endtime(self, time):
        self.endtime = time

    def init_scene(self):
        print(EventReport("Info", "Init Scene"))
        self.sensors = []
        num_sensors = len(c["sensor"])
        for i in range(0, num_sensors):
            s1 = Sensor(i, c["sensor"][i]["name"], c["sensor"][i]["readlatency"], c["sensor"][i]["period"],
                        c["sensor"][i]["pin"])
            self.sensors.append(s1)

        self.set_endtime(c["interval"]["M"])
        self.bought_data = c["params"]["D"]

        print(self.sensors)

        for i in range(0, num_sensors):
            s1 = self.sensors[i]
            CircuitsApp.timers["sense"] = Timer(s1.period, SenseEvent(s1, self.readings_queue), persist=False).register(self)

        CircuitsApp.timers["upload"] = Timer(c["interval"]["upload"], UploadEvent(self.readings_queue), persist=False).register(self)

    def started(self, component):
        while True:
            break
            try:
                actuatorClient = mqttc.Client()
                actuatorClient.on_connect = on_connect
                actuatorClient.on_message = on_message
                actuatorClient.connect(MQTT_BROKER_HOSTNAME, 1883, 60)
                actuatorClient.loop_start()
                print(EventReport("Info", "Started."))
                print(EventReport("Tx", str(get_tx_bytes(TX_MEDIUM))))
                break
            except gaierror:
                print(EventReport("Error", "Failure connecting to MQTT controller"))
            time.sleep(TIMEOUT_MQTT_RETRY)
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
            print (EventReport("Control", "PAUSE EXECUTION received."))
            CircuitsApp.h1.unregister()
            CircuitsApp.h2.unregister()
            CircuitsApp.h3.unregister()
            CircuitsApp.unregister()
            print(EventReport("Info", "Execution paused."))

        if (parsed_json["camera"] == "Y"):
            print(EventReport("Control", "TAKE PICTURE received."))
            newstr = "image" + str(time.time()) + ".jpg"
            try:
                take_picture(newstr)
                print(EventReport("Info", "Picture taken."))
            except:
                print(EventReport("Error", "picture."))

        print(EventReport("Info", "Received a control string."))
        print(parsed_json)
    except:
        print("From topic: " + msg.topic + " INVALID DATA")


CircuitsApp = App()
CircuitsApp.run()
if __name__ == '__main__':
    (App()).run()
    log.info("Keyboard Exit.")
