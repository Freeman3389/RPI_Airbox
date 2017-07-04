#! /usr/bin/python
# Originally Written by Dan Mandle http://dan.mandle.me September 2012
# Modified by Freeman Lee
# License: GPL 2.0

import os, time, sys, logging, pdb
import threading
from gps import *
from time import *
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler

gpsd = None                  #seting the global variable
os.system('clear')           #clear the terminal (optional)
sensor_location  = "living-room"
sensor_readings_list  = ["latitude", "longitude", "altitude"]
record_types_list = ["latest","history"]
base_path  = "/opt/RPi_Airbox/monitor_web/sensor-values/test/"
csv_entry_format  = "{:%Y-%m-%d %H:%M:%S},{:0.1f}\n"
sec_between_log_entries  = 300
latest_reading_value = []
latest_latitude  = 0.0
latest_longtitude  = 0.0
latest_altitude  = 0.0
latest_value_datetime   = None
file_handle   = None

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


def write_header(file_handle, csv_header):
    file_handle.write(csv_header)

def write_value(file_handle, datetime, value):
    line = csv_entry_format.format(datetime, value)
    file_handle.write(line)
    file_handle.flush()

def open_file_ensure_header(file_path, mode, csv_header):
    f = open(file_path, mode, os.O_NONBLOCK)
    if os.path.getsize(file_path) <= 0:
        write_header(f, csv_header)
    return f

def write_latest_value():
    with open_file_ensure_header(latest_gps_file_path, 'w', csv_header_gps) as f_latest_value:  #open and truncate
        write_value(f_latest_value, latest_value_datetime, latest_latitude, latest_longitude, latest_altitude)

if __name__ == '__main__':
    gpsp = GpsPoller() # create the thread
    print "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi..."
    create timer that is called every n seconds, without accumulating delays as when using sleep
    scheduler = BackgroundScheduler()
    scheduler.add_job(write_hist_value_callback, 'interval', seconds=sec_between_log_entries)
    scheduler.start()
    print "Started interval timer which will be called the first time in {0} seconds.".format(sec_between_log_entries);
    f_history_values =[]
    for index, reading in enumerate(sensor_readings_list, start=0):
        f_history_values.append(open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading')))
    try:
        gpsp.start() # start it up
        while True:
            #It may take a second or two to get good data
            #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc
            os.system('clear')
            latest_latitude = gpsd.fix.latitude
            latest_longitude = gpsd.fix.longitude
            latest_altitude = gpsd.fix.altitude
            if latest_latitude is not None and latest_longitude is not None and latest_altitude is not None:
                latest_reading_value = list(latest_latitude, latest_longitude, latest_altitude)
                latest_value_datetime = datetime.today()
                write_latest_value()
            time.sleep(300) #set to whatever

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
        scheduler.shutdown()
        latest_reading_value=[]
        latest_file_path = None
        history_file_path = None
    except IOError as ioer:
        print  ioer + " , wait 10 seconds to restart."
        latest_reading_value = [0,0]
        time.sleep(10)
        pass
