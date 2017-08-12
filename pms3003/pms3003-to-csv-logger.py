"""This script will get PlantPower PMS3003 (G3) sensor readings, and write to csv files."""
# !/bin/python
# -*- coding: utf-8 -*-
# Originally written by Thomas Tsai
# This script was first published at: https://github.com/Thomas-Tsai/pms3003-g3
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0

import os
import serial
import time
import sys
import logging
import syslog
import json
import atexit
from struct import *
from datetime import datetime, date
from array import *

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = str(configs['global']['sensor_location'])
data_path = str(configs['global']['base_path'] + configs['global']['csv_path'])
enable_history = int(configs['global']['enable_history'])
sensor_name = str(configs['pms3003']['sensor_name'])
sensor_readings_list = configs[sensor_name]['sensor_readings_list']
latest_log_interval = int(configs[sensor_name]['latest_log_interval'])
csv_entry_format = configs[sensor_name]['csv_entry_format']
pid_file = str(configs['global']['base_path']) + sensor_name + '.pid'
serial_device = configs[sensor_name]['serial_device']
# Initial variables
latest_value_datetime = None
syslog.openlog(sys.argv[0], syslog.LOG_PID)
debug = 0  # class g3sensor debug mode
air = None

# work for pms3003
# data structure: https://github.com/avaldebe/AQmon/blob/master/Documents/PMS3003_LOGOELE.pdf
# fix me: the format is different between /dev/ttyUSBX(USB to Serial) and /dev/ttyAMA0(GPIO RX)
#          ttyAMA0:0042 004d 0014 0022 0033
#          ttyUSB0:4d42 1400 2500 2f00


class g3sensor():
    """Define PMS3003 Sensor class to get reading values."""
    def __init__(self):
        if debug:
            print "init"
        self.endian = sys.byteorder

    def conn_serial_port(self, device):
        if debug:
            print device
        self.serial = serial.Serial(device, baudrate=9600)
        if debug:
            print "conn ok"

    def check_keyword(self):
        if debug:
            print "check_keyword"
        while True:
            token = self.serial.read()
            token_hex = token.encode('hex')
            if debug:
                print token_hex
            if token_hex == '42':
                if debug:
                    print "get 42"
                token2 = self.serial.read()
                token2_hex = token2.encode('hex')
                if debug:
                    print token2_hex
                if token2_hex == '4d':
                    if debug:
                        print "get 4d"
                    return True
                elif token2_hex == '00':
                    if debug:
                        print "get 00"
                    token3 = self.serial.read()
                    token3_hex = token3.encode('hex')
                    if token3_hex == '4d':
                        if debug:
                            print "get 4d"
                        return True

    def vertify_data(self, data):
        if debug:
            print data
        n = 2
        sum = int('42', 16) + int('4d', 16)
        for i in range(0, len(data) - 4, n):
            sum = sum + int(data[i:i + n], 16)
        versum = int(data[40] + data[41] + data[42] + data[43], 16)
        if debug:
            print sum
        if debug:
            print versum
        if sum == versum:
            print "data correct"

    def read_data(self):
        data = self.serial.read(22)
        data_hex = data.encode('hex')
        if debug:
            self.vertify_data(data_hex)
        pm1_cf = int(data_hex[4] + data_hex[5] + data_hex[6] + data_hex[7], 16)
        pm25_cf = int(data_hex[8] + data_hex[9] +
                      data_hex[10] + data_hex[11], 16)
        pm10_cf = int(data_hex[12] + data_hex[13] +
                      data_hex[14] + data_hex[15], 16)
        pm1 = int(data_hex[16] + data_hex[17] +
                  data_hex[18] + data_hex[19], 16)
        pm25 = int(data_hex[20] + data_hex[21] +
                   data_hex[22] + data_hex[23], 16)
        pm10 = int(data_hex[24] + data_hex[25] +
                   data_hex[26] + data_hex[27], 16)
        if debug:
            print "pm1_cf: " + str(pm1_cf)
        if debug:
            print "pm25_cf: " + str(pm25_cf)
        if debug:
            print "pm10_cf: " + str(pm10_cf)
        if debug:
            print "pm1: " + str(pm1)
        if debug:
            print "pm25: " + str(pm25)
        if debug:
            print "pm10: " + str(pm10)
        data = (pm1_cf, pm10_cf, pm25_cf, pm1, pm10, pm25)
        self.serial.close()
        return data

    def read(self, argv):
        tty = argv[0:]
        self.conn_serial_port(tty)
        if self.check_keyword() == True:
            self.data = self.read_data()
            if debug:
                print self.data
            return self.data


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
    """Pass kind of reading and type to get return parameters."""
    line = csv_entry_format.format(datetime, value)
    file_handle.write(line)
    file_handle.flush()


def open_file_write_header(file_path, mode, csv_header):
    """Pass contents and datetime to write into target file."""
    f = open(file_path, mode, os.O_NONBLOCK)
    if os.path.getsize(file_path) <= 0:
        f.write(csv_header)
    return f


def write_latest_value(latest_value_datetime):
    """For while loop in main() to write latest value into latest csv file."""
    global latest_reading_value
    i = 0
    for reading in sensor_readings_list:
        with open_file_write_header(get_readings_parameters(reading, 'latest_file_path'), 'w', get_readings_parameters(reading, 'csv_header_reading')) as f_latest_value:
            write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
        i += 1
    i = 0


def write_hist_value(latest_value_datetime):
    """Append latest value into history csv file."""
    global latest_reading_value
    f_history_values = []
    for index, reading in enumerate(sensor_readings_list, start=0):
        f_history_values.append(open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))
    for f, v in zip(f_history_values, latest_reading_value):
        write_value(f, latest_value_datetime, v)


if __name__ == '__main__':
    air = g3sensor()
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
        global latest_reading_value
        latest_reading_value = ()
        pmdata = 0
        try:
            pmdata = air.read(serial_device)
            if pmdata != 0:
                latest_reading_value = pmdata
                latest_value_datetime = datetime.today()
                write_latest_value(latest_value_datetime)
                if enable_history == 1:
                    write_hist_value(latest_value_datetime)
                else:
                    pass
            write_pidfile()
            time.sleep(latest_log_interval)
        except IOError as ioer:
            syslog.syslog(syslog.LOG_INFO, ioer + " , wait 10 seconds to restart.")
            latest_reading_value = []
            time.sleep(10)
        except KeyboardInterrupt:
            latest_reading_value = []
            sys.exit(0)
        finally:
            pmdata = 0
