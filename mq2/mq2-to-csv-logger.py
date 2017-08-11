"""This script will get MQ2 sensor readings to write csv files."""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# Originally Written by Dan Mandle http://dan.mandle.me September 2012
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0
from mq import *
from array import *
from datetime import datetime
import sys
import time
import logging
import syslog
import json
import os
import atexit

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = str(configs['global']['sensor_location'])
data_path = str(configs['global']['base_path'] + configs['global']['csv_path'])
enable_history = int(configs['global']['enable_history'])
sensor_name = str(configs['mq2']['sensor_name'])
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
    #pdb.set_trace()
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


def main():
    """Execute main function"""
    try:
        syslog.syslog(syslog.LOG_INFO, "Get MQ2 Sensor Readings.")

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
        mq = MQ()
        while True:
            latest_reading_value = list(mq.MQPercentage().values())
            latest_value_datetime = datetime.today()
            write_latest_value(latest_value_datetime)
            if enable_history == 1:
                write_hist_value(latest_value_datetime)
            else:
                pass
            write_pidfile()
            time.sleep(latest_log_interval)

    except IOError as ioer:
        syslog.syslog(syslog.LOG_WARNING, ioer + " , wait 10 seconds to restart.")
        latest_reading_value = []
        time.sleep(10)

    except KeyboardInterrupt:
        latest_reading_value = []
        sys.exit(0)

if __name__ == "__main__":
    main()
