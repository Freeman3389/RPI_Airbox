"""This script will get GPS coordinates and upload sensor data by MQTT."""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# written by Freeman Lee
# Version 0.1.0 @ 2017.8.11
# License: GPL 2.0
import serial
import time
import datetime
import threading
import os
import json
import csv
import syslog
import atexit
import sys
import paho.mqtt.client as mqtt
from uuid import getnode as get_mac

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = str(configs['global']['sensor_location'])
data_path = str(configs['global']['base_path'] + configs['global']['csv_path'])
sensor_name = str(configs['mqtt']['sensor_name'])
update_interval = int(configs[sensor_name]['update_interval'])
latest_log_interval = int(configs[sensor_name]['update_interval'])
mqtt_server = str(configs[sensor_name]['mqtt_server'])
mqtt_port = int(configs[sensor_name]['mqtt_port'])
username = str(configs[sensor_name]['username'])
passwd = str(configs[sensor_name]['passwd'])
pid_file = str(configs['global']['base_path']) + sensor_name + '.pid'

# Global variables intialization
syslog.openlog(sys.argv[0], syslog.LOG_PID)

class Setting:
    def __init__(self):
        #system general setting
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.username = username
        self.passwd = passwd
        self.app = "RPi_Airbox"
        self.device_id = self.app + '_' + format(get_mac(), 'x')[-6:]
        self.sensor_types = ['temperature', 'humidity', 'pm25-at', 'pm10-at', 'pm1-at']

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
    """Execute main function"""
    sEtting = Setting()
    try:
        global localtime
        sensor_types = sEtting.sensor_types
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
        write_pidfile()
        for sensor in sensor_types:
            payload_str = get_reading_csv(sensor)
            topic = sEtting.device_id + "/" + sensor
            mqttc = mqtt.Client(sEtting.device_id)
            mqttc.username_pw_set(username, password=passwd)
            mqttc.connect(sEtting.mqtt_server, sEtting.mqtt_port, 60)
            #Publishing to MQTT broker
            mqttc.loop_start()
            localtime = datetime.datetime.now()
            mqttc.publish(topic, payload_str, qos=0, retain=False)
            time.sleep(1)

        mqttc.loop_stop()
        mqttc.disconnect()
        time.sleep(update_interval)

    except IOError, ioer:
        syslog.syslog(syslog.LOG_WARNING, "Main thread was died: IOError: %s" % (ioer))
        pass

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
