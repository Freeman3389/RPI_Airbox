#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.07.15
import os
import time
import csv
import sys
import syslog
import json
import platform
import atexit
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from luma.core.virtual import terminal
from PIL import ImageFont
from array import *

# Get settings from '../settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
data_path = configs['global']['base_path'] + configs['global']['csv_path']
sensor_location = configs['global']['sensor_location']
sensor_name = str(configs['sh1106']['sensor_name'])
update_interval = int(configs[sensor_name]['update_interval'])
font_name = str(configs[sensor_name]['font_name'])
font_size = int(configs[sensor_name]['font_size'])
device_height = int(configs[sensor_name]['device_height'])
i2c_port = int(configs[sensor_name]['i2c_port'])
i2c_address = int(configs[sensor_name]['i2c_address'], 16)
pid_file = str(configs['global']['base_path']) + sensor_name + '.pid'
# initial variables
syslog.openlog(sys.argv[0], syslog.LOG_PID)
latest_reading_values = []
serial = i2c(port=i2c_port, address=i2c_address)
device = sh1106(serial)


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
        # use custom font
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fonts', font_name))
        font2 = ImageFont.truetype(font_path, font_size)
        # define display string of each line
        str_lines = []
        str_lines.append('Host: ' + platform.node())
        str_lines.append(time.strftime('%Y/%m/%d %H:%M:%S'))
        str_lines.append('eth0: ' +  os.popen('ip addr show ' + 'eth0' + ' | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip())
        str_lines.append('wlan0: ' +  os.popen('ip addr show ' + 'wlan0' + ' | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'').read().strip())
        str_lines.append('Temp: ' + str(get_reading_csv('temperature')) + ' c')
        str_lines.append('Humi: ' + str(get_reading_csv('humidity')) + ' %')
        str_lines.append('Smoke: ' + str(get_reading_csv('Smoke')) + ' ppm')
        str_lines.append('CO: ' + str(get_reading_csv('CO')) + ' ppm')
        str_lines.append('LPG: ' + str(get_reading_csv('GAS-LPG')) + ' ppm')

        term = terminal(device, font2)

        for i in range(0, len(str_lines), 1):
            term.println(str_lines[i])
            time.sleep(update_interval)
        time.sleep(update_interval)
        term.clear()
        write_pidfile()
        time.sleep(update_interval)


except IOError, ioer:
    syslog.syslog(syslog.LOG_WARNING, "Main thread was died: IOError: %s" % (ioer))
    pass

except KeyboardInterrupt:
    sys.exit(0)
