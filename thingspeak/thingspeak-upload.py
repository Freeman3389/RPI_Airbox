"""This script will get sensor values from csv files and upload to Thingspeak platform"""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# Originally written by Thomas Tsai
# This script was first published at: https://github.com/Thomas-Tsai/pms3003-g3
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0

import time
import sys
import httplib
import urllib
import csv
import syslog
import json
import os
import atexit
from array import *

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
data_path = configs['global']['base_path'] + configs['global']['csv_path']
sensor_location = configs['global']['sensor_location']
update_interval = int(configs['thingspeak']['update_interval'])
api_key = str(configs['thingspeak']['api_key'])
pid_file = str(configs['global']['base_path']) + str(configs['thingspeak']['sensor_name']) + '.pid'
# Initial variables
sensors = ['temperature', 'humidity', 'pm1-at', 'pm25-at', 'pm10-at']  # Define all the sensor readings uploading to Thingspeak

syslog.openlog(sys.argv[0], syslog.LOG_PID)


def get_reading_csv(sensor):
    """Get sensor readings from latest value csv files in sensor-value folder."""
    sensor_reading = None
    csv_path = data_path + sensor + '_' + sensor_location + '_latest_value.csv'
    with open(csv_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader)  # skip header of csv file
        for row in csvreader:
            sensor_reading = row[1]  # get second value
    return sensor_reading


def main():
    while True:
        try:
            latest_reading_values = []
            syslog.syslog(syslog.LOG_INFO,
                          "Begin to upload Sensor values onto Thingspeak.")
            for sensor in sensors:
                latest_reading_values.append(get_reading_csv(sensor))
        except IOError as ioer:
            syslog.syslog(syslog.LOG_WARNING, ioer +
                          " , wait 10 seconds to restart.")
            time.sleep(10)
            continue

        # thingspeak
        params_public = urllib.urlencode(
            {'field1': latest_reading_values[0], 'field2': latest_reading_values[1],
             'field3': latest_reading_values[2], 'field4': latest_reading_values[3],
             'field5': latest_reading_values[4], 'key': api_key})
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        try:
            conn = httplib.HTTPConnection("api.thingspeak.com:80")
            conn.request("POST", "/update", params_public, headers)
            res = conn.getresponse()
            syslog.syslog(syslog.LOG_INFO, 'Thingspeak HTTP Response: ' + str(res.status) + ' ' + res.reason)
            data = res.read()
        finally:
            conn.close()
            params_public = {}
            latest_reading_values = []
            time.sleep(update_interval)

if __name__ == "__main__":
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
        main()
        write_pidfile()
    except KeyboardInterrupt:
        sys.exit(0)
