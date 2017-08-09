import serial
import time
import datetime
import threading
import os
import json
import csv
import pdb
import paho.mqtt.client as mqtt
from gps import *
# Global variables intialization
gpsd = None

class Setting:
    def __init__(self):
        #system general setting
        self.debug_enable = 0 #Default:0, 0: debug disable , 1: debug enable
        #self.mqtt_topic="LASS/#"   #REPLACE: to your sensor topic
        #self.mqtt_topic="LASS/Test/+"  #REPLACE: to your sensor topic, it do not subscribe device id's channel
        self.mqtt_server = "gpssensor.ddns.net"
        self.mqtt_port = 1883
        self.mqtt_topic = "LASS/Test/#"  #Default: LASS/Test/+ , REPLACE: to your sensor topic, it do not subscribe device id's channel
        self.device_id = "RPi_Airbox_000000" #Default: YOUR_DEVICE_NAME, REPLACE: to your device id
        self.clientid="RPiAirboxYM_1502271751"
        self.username="e119d4cd-4b84-410f-b598-282ae59c9d2a"
        self.passwd="r:20dae1c1ab24b0f84ea5bfcbfd47e9b2"
        self.ver_format = 3
        self.fake_gps = 1
        self.app = "RPi_Airbox"
        self.ver_format = 3 #Default 3,: filter parameter when filter_par_type=2
        self.ver_app = "0.8.3"
        self.device = "RaspberryPi_3"
        self.sensor_types = ['temperature', 'humidity', 'pm25-at', 'pm10-at']
        self.fgps_lon = 121.3713162
        self.fgps_lat = 25.055752
        self.fgps_alt = 0.0

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
    #example payload
    #ver_format=3|FAKE_GPS=0|app=PM25|ver_app=0.8.3|device_id=Prodisky|tick=2344468811|date=2017-08-07|time=08:54:25|device=LinkItONE|s_0=78423.00|s_1=100.00|s_2=1.00|s_3=0.00|s_4=4.00|s_d0=10.00|s_t0=38.20|s_h0=91.10|s_d1=13.00|gps_lat=24.101681|gps_lon=120.395232|gps_fix=1|gps_num=16|gps_alt=126
    global localtime
    global value_dict
    global sEtting
    sensor_types = sEtting.sensor_types
    sensor_values = []
    value_dict = {}
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
    else:
        value_dict["gps_lat"] = get_gps()[0]
        value_dict["gps_lon"] = get_gps()[1]
        value_dict["gps_alt"] = get_gps()[2]
    value_dict["gps_fix"] = 0
    value_dict["gps_num"] = 0
    if str_type == 'raw':
        payload_str = "|".join(["=".join([key, str(val)]) for key, val in value_dict.items()])

    return payload_str

def get_reading_csv(sensor):
    """Get sensor readings from latest value csv files in sensor-value folder."""
    with open(os.path.abspath(__file__ + '/../..') + '/settings.json') as json_handle:
        configs = json.load(json_handle)
    data_path = configs['global']['base_path'] + configs['global']['csv_path']
    sensor_location = configs['global']['sensor_location']
    sensor_reading = None
    csv_path = data_path + sensor + '_' + sensor_location + '_latest_value.csv'
    with open(csv_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader)  # skip header of csv file
        for row in csvreader:
            sensor_reading = row[1]  # get second value
    return sensor_reading

def get_gps():
    gpsp = GpsPoller()
    try:
        gpsp.start()
        if gpsd.fix.mode == 1:
            return sEtting.fgps_lat, sEtting.fgps_lon, sEtting.fgps_alt
        if gpsd.fix.mode == 2:
            return gpsd.fix.latitude, gpsd.fix.longitude, sEtting.fgps_alt
        if gpsd.fix.mode == 3:
            return gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.altitude
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing


def main():
    global sEtting
    global localtime
    global value_dict
    sEtting = Setting()
    localtime = datetime.datetime.now()
    payload_str = data_process('raw')
    pdb.set_trace()
    mqttc = mqtt.Client(sEtting.clientid)
    mqttc.username_pw_set(sEtting.username, password=sEtting.passwd)
    #Publishing to QIoT
    mqttc.loop_start()
    while mqttc.loop() == 0:
        msg = json.JSONEncoder().encode(payload_str)
        mqttc.connect(sEtting.mqtt_server, sEtting.mqtt_port, 60)
        mqttc.publish(sEtting.mqtt_topic, payload=msg, qos=0, retain=False)
    time.sleep(5)


if __name__ == "__main__":
    main()
