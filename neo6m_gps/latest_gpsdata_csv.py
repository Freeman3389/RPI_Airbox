#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import os
import threading
from gps import *
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler 
 
gpsd = None #seting the global variable
os.system('clear') #clear the terminal (optional)
sensor_location              = "living-room"
latest_gps_file_path         = "sensor-values/gps_" + sensor_location + "_latest_value.csv"
csv_header_gps               = "timestamp,latitude,longitude,altitude\n"
csv_entry_format             = "{:%Y-%m-%d %H:%M:%S},{:0.1f}\n"
sec_between_log_entries      = 60
latest_latitude              = 0.0
latest_longtitude            = 0.0
latest_altitude              = 0.0
latest_value_datetime        = None
file_handle                  = None
 
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
    global sensor_location, latest_gps_file_path, 
    #print "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi..."
    #create timer that is called every n seconds, without accumulating delays as when using sleep
    #scheduler = BackgroundScheduler()
    #scheduler.add_job(write_hist_value_callback, 'interval', seconds=sec_between_log_entries)
    #scheduler.start()
    #print "Started interval timer which will be called the first time in {0} seconds.".format(sec_between_log_entries);
    
    try:
        gpsp.start() # start it up
    while True:
        #It may take a second or two to get good data
   
        os.system('clear')
        latitude = gpsd.fix.latitude
        longitude = gpsd.fix.longitude
	altitude = gpsd.fix.altitude
	if latitude is not None and longitude is not None and altitude is not None:
            latest_latitude, latest_longitude, latest_altitude = latitude, longitude, altitude
            latest_value_datetime = datetime.today()
            write_latest_value()
        time.sleep(5) #set to whatever
    except (IOError, SystemExit): #when the file path doesn't exist
        print "\nlatest csv file doesn't exist!"
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nUser interrupt. Killing Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing

    finally:
        print "Done.\nExiting."

