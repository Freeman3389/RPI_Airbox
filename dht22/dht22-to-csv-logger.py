"""This script will get DHT22 sensor readings, and write to csv files."""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# Originally written by David Neuy
# Version 0.1.0 @ 03.12.2014
# This script was first published at: http://www.home-automation-community.com/
# You may republish it as is or publish a modified version only when you
# provide a link to 'http://www.home-automation-community.com/'.
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0


import os
import sys
import Adafruit_DHT
import time
import logging
import syslog
import json
from datetime import datetime
# install dependency with 'sudo easy_install apscheduler' NOT with 'sudo pip install apscheduler'
from apscheduler.schedulers.background import BackgroundScheduler

# Get settings from 'settings.json'
with open('/opt/RPi_Airbox/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = configs['global']['sensor_location']
sensor_readings_list = configs['dht22']['sensor_readings_list']
data_path = configs['global']['base_path'] + configs['global']['csv_path']
latest_log_interval = int(configs['dht22']['latest_log_interval'])
history_log_interval = int(configs['dht22']['history_log_interval'])
csv_entry_format = configs['dht22']['csv_entry_format']
# Initial variables
latest_reading_value = []
latest_value_datetime = None
syslog.openlog(sys.argv[0], syslog.LOG_PID)
# DHT22 specific parameters
sensor = Adafruit_DHT.AM2302
pin = 4


def get_sensor_readings(sensor, pin):
    """Pass parameters of DHT22 sensor and GPIO #, get Reading vaules."""
    dht22_readings = Adafruit_DHT.read_retry(sensor, pin)
    if all(dht22_readings):
        return (map(lambda x: float('%0.2f' % x), dht22_readings))
    else:
        syslog.syslog(syslog.LOG_WARNING, "CANNOT get correct readings from DHT22 sensor!")
        pass


def get_readings_parameters(reading, type):
    """Pass kind of reading and type to get return parameters."""
    if type == 'history_file_path':
        return data_path + reading + "_" + sensor_location + "_log_" + datetime.today().strftime('%Y') + ".csv"
    elif type == 'latest_file_path':
        return data_path + reading + "_" + sensor_location + "_latest_value.csv"
    elif type == 'csv_header_reading':
        return "timestamp," + reading + "\n"
    else:
        return None


def write_value(file_handle, datetime, value):
    """Pass contents and datetime to write into target file."""
    line = csv_entry_format.format(datetime, value)
    file_handle.write(line)
    file_handle.flush()


def open_file_write_header(file_path, mode, csv_header):
    """Check if the target file is new, and write header."""
    f = open(file_path, mode, os.O_NONBLOCK)
    if os.path.getsize(file_path) <= 0:
        f.write(csv_header)
    return f


def write_hist_value_callback():
    """For apscheduler to append latest value into history csv file."""
    for f, v in zip(f_history_values, latest_reading_value):
        write_value(f, latest_value_datetime, v)


def write_latest_value():
    """For while loop in main() to write latest value into latest csv file."""
    i = 0
    for reading in sensor_readings_list:
        with open_file_write_header(get_readings_parameters(reading, 'latest_file_path'), 'w', get_readings_parameters(reading, 'csv_header_reading')) as f_latest_value:
            write_value(f_latest_value, latest_value_datetime,
                        latest_reading_value[i])
        i += 1
    i = 0


f_history_values = []
for index, reading in enumerate(sensor_readings_list, start=0):
    f_history_values.append(open_file_write_header(get_readings_parameters(
        reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))

syslog.syslog(syslog.LOG_INFO, "Ignoring first 2 sensor values to improve quality...")
for x in range(2):
    Adafruit_DHT.read_retry(sensor, pin)

syslog.syslog(syslog.LOG_INFO, "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi...")
# create timer that is called every n seconds, without accumulating delays as when using sleep
logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.add_job(write_hist_value_callback, 'interval',
                  seconds=history_log_interval)
scheduler.start()
syslog.syslog(syslog.LOG_INFO, 'Started interval timer which will be called the first time in {0} seconds.'.format(history_log_interval))

try:
    while True:
        latest_reading_value = get_sensor_readings(sensor, pin)
        latest_value_datetime = datetime.today()
        write_latest_value()
        time.sleep(latest_log_interval)
except IOError as ioer:
    syslog.syslog(syslog.LOG_WARNING, ioer + " , wait 10 seconds to restart.")
    latest_reading_value = []
    time.sleep(10)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    latest_reading_value = []
    latest_file_path = None
    history_file_path = None
