# I am adding python 3 codes here

from __future__ import print_function
import sys
import time
import datetime
import os
import json
import logging.config
import logging

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def setup_logging(
        default_path='config/logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)





# OS Specific Functions
#----------------------
def get_tx_bytes(transmission_medium):
    try:
        astring = 'cat /sys/class/net/' + transmission_medium + '/statistics/tx_bytes'
        return long(os.popen(astring).read())
    except:
        return 0

# Time Related
#-------------

def get_time_as_string(atime):
    return datetime.datetime.fromtimestamp(atime).strftime('%Y-%m-%d %H:%M:%S')



def edit_calib_config(fieldname, value):
    with open('config/calibration.json', 'r') as f:
        config = json.load(f)
    # edit the data
    config[fieldname] = value
    # write it back to the file
    with open('config/calibration.json', 'w') as f:
        json.dump(config, f)


def read_calib_config(fieldname):
    with open('config/calibration.json', 'r') as f:
        config = json.load(f)
    return config[fieldname]


'''
#COMMENT_IN_PC

import time
import picamera

def take_picture(pic_name='image.jpg', delay=0):
    #pic_location = '/home/pi/workshop/camera/'
    pic_location = 'pictures/'
    pic_location = pic_location + pic_name
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(delay)
        camera.capture(pic_location)
        camera.stop_preview()

#COMMENT_IN_PC
'''
def take_picture(pic_name='image.jpg', delay=0):
    ''''''

#pic_location = '/home/pi/workshop/camera/image.jpg'
#take_picture()
