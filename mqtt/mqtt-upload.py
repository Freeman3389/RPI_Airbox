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
import collections
import pdb
import syslog
import atexit
import paho.mqtt.client as mqtt
from gps import *
from uuid import getnode as get_mac

# Get settings from 'settings.json'
with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
    configs = json.load(json_handle)
sensor_location = str(configs['global']['sensor_location'])
data_path = str(configs['global']['base_path'] + configs['global']['csv_path'])
fake_gps = int(configs['global']['fake_gps'])
fgps_lat = float(configs['global']['fgps_lat'])
fgps_lon = float(configs['global']['fgps_lon'])
fgps_alt = float(configs['global']['fgps_alt'])
sensor_name = str(configs['mqtt']['sensor_name'])
debug_enable = int(configs[sensor_name]['debug_enable'])
update_interval = int(configs[sensor_name]['update_interval'])
latest_log_interval = int(configs[sensor_name]['update_interval'])
mqtt_server = str(configs[sensor_name]['mqtt_server'])
mqtt_port = int(configs[sensor_name]['mqtt_port'])
mqtt_topic = str(configs[sensor_name]['mqtt_topic'])
clientid = str(configs[sensor_name]['clientid'])
username = str(configs[sensor_name]['username'])
passwd = str(configs[sensor_name]['passwd'])
pid_file = str(configs['global']['base_path']) + sensor_name + '.pid'

# Global variables intialization
syslog.openlog(sys.argv[0], syslog.LOG_PID)
gpsd = None

class Setting:
    def __init__(self):
        #system general setting
        self.debug_enable = debug_enable
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.fake_gps = fake_gps
        self.fgps_lon = fgps_lon
        self.fgps_lat = fgps_lat
        self.fgps_alt = fgps_alt
        self.clientid = clientid
        self.username = username
        self.passwd = passwd
        self.app = "RPi_Airbox"
        self.device_id = self.app + '_' + format(get_mac(), 'x')[-6:]
        self.ver_format = 3 #Default 3,: filter parameter when filter_par_type=2
        self.ver_app = "0.8.3"
        self.device = "RaspberryPi_3"
        self.sensor_types = ['temperature', 'humidity', 'pm25-at', 'pm10-at']
        self.payload_header = ('ver_format', 'FAKE_GPS', 'app', 'ver_app', 'device_id', 'date', 'time', 'device', 's_d0', 's_t0', 's_h0', 's_d1', 'gps_lat', 'gps_lon', 'gps_fix', 'gps_num', 'gps_alt')


class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd #bring it in scope
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        self.current_value = None
        self.running = True #setting the thread running to true

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer


def data_process(str_type):
    """parse the data and form the related variables"""
    global localtime
    global value_dict
    global sEtting
    sensor_types = sEtting.sensor_types
    sensor_values = []
    value_dict = collections.OrderedDict.fromkeys(sEtting.payload_header)
    value_dict["ver_format"] = sEtting.ver_format
    value_dict["FAKE_GPS"] = sEtting.fake_gps
    value_dict["app"] = sEtting.app
    value_dict["ver_app"] = sEtting.ver_app
    value_dict["device_id"] = sEtting.device_id
    value_dict["date"] = localtime.strftime("%Y-%m-%d")
    value_dict["time"] = localtime.strftime("%H:%M:%S")
    value_dict["device"] = sEtting.device

    for sensor in sensor_types:
        if sensor == 'pm25-at':
            value_dict["s_d0"] = get_reading_csv(sensor)
        elif sensor == 'temperature':
            value_dict["s_t0"] = get_reading_csv(sensor)
        elif sensor == 'humidity':
            value_dict["s_h0"] = get_reading_csv(sensor)
        elif sensor == 'pm10-at':
            value_dict["s_d1"] = get_reading_csv(sensor)
        else:
            print 'Not support sensor type.'
    if sEtting.fake_gps == 1:
        value_dict["gps_lat"] = sEtting.fgps_lat
        value_dict["gps_lon"] = sEtting.fgps_lon
        value_dict["gps_alt"] = sEtting.fgps_alt
        value_dict["gps_fix"] = 0
    else:
        value_dict["gps_lat"] = get_gps()[0]
        value_dict["gps_lon"] = get_gps()[1]
        value_dict["gps_alt"] = get_gps()[2]
        value_dict["gps_fix"] = gpsd.fix.mode
    value_dict["gps_num"] = 0
    if debug_enable == '0':
        payload_str = "|" + "|".join(["=".join([key, str(val)]) for key, val in value_dict.items()])
    elif debug_enable == '1':
        payload_str = ",".join(["=".join([key, str(val)]) for key, val in value_dict.items()])
        print 'payload_str = ' + payload_str
    return payload_str

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

def get_gps():
    """check fix status of gpsd"""
    if gpsd.fix.mode == 1:
        return float(sEtting.fgps_lat), float(sEtting.fgps_lon), float(sEtting.fgps_alt)
    if gpsd.fix.mode == 2:
        return gpsd.fix.latitude, gpsd.fix.longitude, float(sEtting.fgps_alt)
    if gpsd.fix.mode == 3:
        return gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.altitude


def main():
    """Execute main function"""
    try:
        global localtime
        global value_dict
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
        mqttc = mqtt.Client(sEtting.clientid)
        mqttc.connect(sEtting.mqtt_server, sEtting.mqtt_port, 60)
        #mqttc.username_pw_set(sEtting.username, password=sEtting.passwd)
        #Publishing to QIoT
        write_pidfile()
        mqttc.loop_start()
        while True:
            localtime = datetime.datetime.now()
            payload_str = data_process('raw')
            #msg = json.JSONEncoder().encode(payload_str)
            (result, mid) = mqttc.publish(sEtting.mqtt_topic, payload_str, qos=0, retain=False)
            time.sleep(update_interval)

        mqttc.loop_stop()
        mqttc.disconnect()

    except IOError, ioer:
        syslog.syslog(syslog.LOG_WARNING, "Main thread was died: IOError: %s" % (ioer))
        pass

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    global sEtting
    global gpsp
    sEtting = Setting()
    if sEtting.fake_gps == 0:
        gpsp = GpsPoller()
    try:
        gpsp.start()
        main()
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."
