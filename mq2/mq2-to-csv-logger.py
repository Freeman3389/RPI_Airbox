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
#import pdb
# install dependency with 'sudo easy_install apscheduler' NOT with 'sudo pip install apscheduler'
from apscheduler.schedulers.background import BackgroundScheduler

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = configs['global']['sensor_location']
sensor_readings_list = configs['mq2']['sensor_readings_list']
data_path = configs['global']['base_path'] + configs['global']['csv_path']
latest_log_interval = int(configs['mq2']['latest_log_interval'])
history_log_interval = int(configs['mq2']['history_log_interval'])
csv_entry_format = configs['mq2']['csv_entry_format']
pid_file = str(configs['global']['base_path']) + str(configs['mq2']['sensor_name']) + '.pid'
# Initial variables
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


f_history_values = []
for index, reading in enumerate(sensor_readings_list, start=0):
    f_history_values.append(open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))


syslog.syslog(syslog.LOG_INFO, "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi...")
# create timer that is called every n seconds, without accumulating delays as when using sleep
logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.add_job(write_hist_value_callback, 'interval',
                  seconds=history_log_interval)
scheduler.start()
syslog.syslog(syslog.LOG_INFO, 'Started interval timer which will be called the first time in {0} seconds.'.format(history_log_interval))


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
        #pdb.set_trace()
        time.sleep(latest_log_interval)
        latest_value_datetime = datetime.today()
        write_latest_value()
        write_pidfile()

except IOError as ioer:
    syslog.syslog(syslog.LOG_WARNING, ioer + " , wait 10 seconds to restart.")
    latest_reading_value = []
    time.sleep(10)

except (KeyboardInterrupt):
    scheduler.shutdown()
    latest_reading_value = []
    latest_file_path = None
    history_file_path = None
    sys.exit(0)
