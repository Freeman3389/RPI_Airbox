"""This script will get DHT22 sensor readings, and write to csv files."""
# !/usr/bin/python
# Originally written by David Neuy
# Version 0.1.0 @ 03.12.2014
# This script was first published at: http://www.home-automation-community.com/
# You may republish it as is or publish a modified version only when you
# provide a link to 'http://www.home-automation-community.com/'.
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30

# install dependency with 'sudo easy_install apscheduler' NOT with 'sudo pip install apscheduler'
import os
import Adafruit_DHT
import time
import logging
import pdb
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# DHT22 specific parameters
sensor = Adafruit_DHT.AM2302
pin = 4
# csv files related parameters
sensor_location = "living-room"
sensor_readings_list = ["humidity", "temperature"]
base_path = "/opt/RPi_Airbox/monitor_web/sensor-values/test/"
csv_entry_format = "{:%Y-%m-%d %H:%M:%S},{:0.1f}\n"
sec_between_log_entries = 60
latest_reading_value = []
latest_value_datetime = None


def get_sensor_readings(sensor, pin):
    """Pass parameters of DHT22 sensor and GPIO #, get Reading vaules."""
    dht22_readings = Adafruit_DHT.read_retry(sensor, pin)
    if all(dht22_readings):
        return (map(lambda x: float('%0.2f' % x), dht22_readings))

# def reading_type_dict(category):
    # generate file_path_dict = {('temperature','latest'):'latest_file_path', ('temperature','history'):'history_file_path' ....})
    # generate csv_header_dict = {'temperature':'Timestamp, Temperature/n', 'humidity':'Timestamp, Humidity/n'}


def get_readings_parameters(reading, type):
    """Pass kind of reading and type to get return parameters."""
    if type == 'history_file_path':
        return (base_path + reading + "_" + sensor_location + "_log_" + datetime.today().strftime('%Y_%m') + ".csv")
    elif type == 'latest_file_path':
        return (base_path + reading + "_" + sensor_location + "_latest_value.csv")
    elif type == 'csv_header_reading':
        return ("timestamp," + reading + "\n")
    else:
        return None


def write_value(file_handle, datetime, value):
    """Pass contents and datetime to write into target file."""
    line = csv_entry_format.format(datetime, value)
    file_handle.write(line)
    file_handle.flush()


def open_file_write_header(file_path, mode, csv_header):
    """Check if the target file is new, and write header."""
    # pdb.set_trace()
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
        pdb.set_trace()
        with open_file_write_header(get_readings_parameters(reading, 'latest_file_path'), 'w', get_readings_parameters(reading, 'csv_header_reading')) as f_latest_value:
            write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
        i += 1
    i = 0


f_history_values = []
for index, reading in enumerate(sensor_readings_list, start=0):
    f_history_values.append(open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))

print "Ignoring first 2 sensor values to improve quality..."
for x in range(2):
    Adafruit_DHT.read_retry(sensor, pin)

print "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi..."
# create timer that is called every n seconds, without accumulating delays as when using sleep
logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.add_job(write_hist_value_callback, 'interval', seconds=sec_between_log_entries)
scheduler.start()
print "Started interval timer which will be called the first time in {0} seconds.".format(sec_between_log_entries);

try:
    while True:
        latest_reading_value = get_sensor_readings(sensor, pin)
        latest_value_datetime = datetime.today()
        write_latest_value()
        time.sleep(60)
except IOError as ioer:
    print ioer + " , wait 10 seconds to restart."
    latest_reading_value = [0, 0]
    time.sleep(10)
    pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    latest_reading_value = []
    latest_file_path = None
    history_file_path = None
