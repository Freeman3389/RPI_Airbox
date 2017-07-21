"""This script will get GPS lat, lon to write to csv files."""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# Originally Written by Dan Mandle http://dan.mandle.me September 2012
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0

import os
import sys
import time
import threading
import syslog
import json
from gps import *
# from time import *
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..' ) + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = configs['global']['sensor_location']
sensor_readings_list = configs['neo6m']['sensor_readings_list']
data_path = configs['global']['base_path'] + configs['global']['csv_path']
latest_log_interval = int(configs['neo6m']['latest_log_interval'])
history_log_interval = int(configs['neo6m']['history_log_interval'])
csv_entry_format = configs['neo6m']['csv_entry_format']
# Initial variables
gpsd = None                  # seting the global variable
latest_reading_value = []
latest_latitude = 0.0
latest_longitude = 0.0
latest_altitude = 0.0
latest_value_datetime = None
file_handle = None
syslog.openlog(sys.argv[0], syslog.LOG_PID)


class GpsPoller(threading.Thread):
    """Create class to get Gps related values."""

    def __init__(self):
        """Define gpsd mode."""
        threading.Thread.__init__(self)
        global gpsd  # bring it in scope
        gpsd = gps(mode=WATCH_ENABLE)  # starting the stream of info
        self.current_value = None
        self.running = True  # setting the thread running to true

    def run(self):
        """Get gpsd info in loop."""
        global gpsd
        while gpsp.running:
            gpsd.next()  # this will continue to loop and grab EACH set of gpsd info to clear the buffer


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
            write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
        i += 1
    i = 0


if __name__ == '__main__':
    gpsp = GpsPoller()  # create the thread
    syslog.syslog(syslog.LOG_INFO, "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi...")
    # create timer that is called every n seconds, without accumulating delays as when using sleep
    scheduler = BackgroundScheduler()
    scheduler.add_job(write_hist_value_callback, 'interval', seconds=history_log_interval)
    scheduler.start()
    syslog.syslog(syslog.LOG_INFO, "Started interval timer which will be called the first time in {0} seconds.".format(history_log_interval))
    f_history_values = []
    for index, reading in enumerate(sensor_readings_list, start=0):
        f_history_values.append(open_file_write_header(get_readings_parameters(
            reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))
    try:
        gpsp.start()  # start it up
        while True:
            # It may take a second or two to get good data
            latest_latitude = gpsd.fix.latitude
            latest_longitude = gpsd.fix.longitude
            latest_altitude = gpsd.fix.altitude
            if latest_latitude != 'nan' and latest_longitude != 'nan' and latest_altitude != 'nan':
                latest_reading_value = [latest_latitude, latest_longitude, latest_altitude]
            elif latest_latitude == 'nan' or latest_longitude == 'nan' or latest_altitude == 'nan':
                latest_reading_value = [0.0, 0.0, 0.0]
                syslog.syslog(syslog.LOG_WARNING, "GPS module CANNOT get precisely location")
            latest_value_datetime = datetime.today()
            write_latest_value()
            time.sleep(latest_log_interval)  # set to whatever

    except (KeyboardInterrupt, SystemExit):  # when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join()  # wait for the thread to finish what it's doing
        scheduler.shutdown()
    except IOError as ioer:
        syslog.syslog(syslog.LOG_WARNING, ioer + " , wait 10 seconds to restart.")
        time.sleep(10)
    finally:
        latest_reading_value = []
        latest_file_path = None
        history_file_path = None
