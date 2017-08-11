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
import atexit
from gps import *
# from time import *
from datetime import datetime
from array import *

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = str(configs['global']['sensor_location'])
data_path = str(configs['global']['base_path'] + configs['global']['csv_path'])
enable_history = int(configs['global']['enable_history'])
sensor_name = str(configs['neo6m']['sensor_name'])
sensor_readings_list = configs[sensor_name]['sensor_readings_list']
latest_log_interval = int(configs[sensor_name]['latest_log_interval'])
csv_entry_format = configs[sensor_name]['csv_entry_format']
pin = int(configs[sensor_name]['gpio_pin'])
pid_file = str(configs['global']['base_path']) + sensor_name + '.pid'

# Initial variables
global latest_reading_value
latest_reading_value = []
latest_value_datetime = None
syslog.openlog(sys.argv[0], syslog.LOG_PID)
gpsd = None


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
    f_csv = open(file_path, mode, os.O_NONBLOCK)
    if os.path.getsize(file_path) <= 0:
        f_csv.write(csv_header)
    return f_csv


def write_latest_value(latest_value_datetim):
    """For while loop in main() to write latest value into latest csv file."""
    global latest_reading_value
    i = 0
    for reading in sensor_readings_list:
        with open_file_write_header(get_readings_parameters(reading, 'latest_file_path'), 'w', get_readings_parameters(reading, 'csv_header_reading')) as f_latest_value:
            write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
        i += 1
    i = 0


def write_hist_value(latest_value_datetime):
    """For apscheduler to append latest value into history csv file."""
    global latest_reading_value
    f_history_values = []
    for index, reading in enumerate(sensor_readings_list, start=0):
        f_history_values.append(open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))
    for f, v in zip(f_history_values, latest_reading_value):
        write_value(f, latest_value_datetime, v)


def get_gps():
    """Check GPSD fix status"""
    if gpsd.fix.mode == 1:
        return configs['global']['fgps_lat'], configs['global']['fgps_lon'], configs['global']['fgps_alt']
    if gpsd.fix.mode == 2:
        return gpsd.fix.latitude, gpsd.fix.longitude, configs['global']['fgps_alt']
    if gpsd.fix.mode == 3:
        return gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.altitude


def main():
    """Execute main function"""
    try:
        def all_done():
            """Define atexit function"""
            pid = str(pid_file)
            os.remove(pid)


        def write_pidfile():
            """Setup PID file"""
            pid = str(os.getpid())
            f_pid = open(pid_file, 'w')
            f_pid.write(pid)
            f_pid.close()


        atexit.register(all_done)
        while True:
            # It may take a second or two to get good data
            latest_reading_value = [get_gps()]
            latest_value_datetime = datetime.today()
            write_latest_value(latest_value_datetime)
            if enable_history == 1:
                write_hist_value(latest_value_datetime)
            else:
                pass
            write_pidfile()
            time.sleep(latest_log_interval)  # set to whatever

    except IOError as ioer:
        syslog.syslog(syslog.LOG_WARNING, ioer + " , wait 10 seconds to restart.")
        time.sleep(10)

    finally:
        latest_reading_value = []


if __name__ == '__main__':
    global gpsp
    gpsp = GpsPoller()  # create the thread
    try:
        gpsp.start()  # start it up
        main()

    except KeyboardInterrupt:  # when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join()  # wait for the thread to finish what it's doing
        sys.exit(0)
