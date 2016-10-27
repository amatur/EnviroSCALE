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

"""
Returns time as a float i.e. 1355563265.81
"""
def get_timestamp():
    st = time.time()
    return ((st))


"""
Print time as "2012-12-15 01:21:05 "
"""


def print_time_now():
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), end="")


"""
Returns time in format 12:01:02
"""


def time_of_now():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')


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
