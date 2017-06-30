# Written by David Neuy
# Version 0.1.0 @ 03.12.2014
# This script was first published at: http://www.home-automation-community.com/
# You may republish it as is or publish a modified version only when you 
# provide a link to 'http://www.home-automation-community.com/'. 

#install dependency with 'sudo easy_install apscheduler' NOT with 'sudo pip install apscheduler'
import os, sys, Adafruit_DHT, time
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler

#DHT22 specific parameters
sensor                       = Adafruit_DHT.AM2302
pin                          = 4
#csv files related parameters
sensor_location              = "living-room"
sensor_readings_list         = ["humidity","temperature"]
record_types_list            = ["latest","history"]
base_path                    = "/opt/RPi_Airbox/monitor_web/sensor-values/"
hist_sensor_file_path        = base_path + sensor_name + "_" + sensor_location + "_log_" + datetime.date.today().strftime('%Y_%m') + ".csv"
latest_sensor_file_path      = base_path + sensor_name + "_" + sensor_location + "_latest_value.csv"
csv_header_readings          =   
csv_entry_format             = "{:%Y-%m-%d %H:%M:%S},{:0.1f}\n"
sec_between_log_entries      = 300
latest_value_datetime        = None


def get_sensor_readings(sensor, pin):
    dht22_readings=Adafruit_DHT.read_retry(sensor, pin)
	if all(dht22_readings):
	    latest_sensor_readings = map(lambda x: float('%0.2f' % x), dht22_readings
	    return (map(lambda X: float('%0.2f' % x), dht22_readings))

def reading_type_dict(category)
    # generate file_path_dict = {('temperature','latest'):'latest_file_path', ('temperature','history'):'history_file_path' ....}
	# generate csv_header_dict = {'temperature':'Timestamp, Temperature/n', 'humidity':'Timestamp, Humidity/n'}
			
		
def get_readings_parameters(reading, type)
    if type == 'history_file_path':
        return (base_path + reading + "_" + sensor_location + "_log_" + datetime.date.today().strftime('%Y_%m') + ".csv")
	elif type == 'latest_file_path':
	    return (base_path + reading + "_" + sensor_location + "_latest_value.csv")
	elif type == 'csv_header_reading'
	    return ("timestamp," + reading + "\n")
	
def write_value(file_handle, datetime, value):
    line = csv_entry_format.format(datetime, value)
    file_handle.write(line)
    file_handle.flush()

def open_file_write_header(file_path, mode, csv_header):
    f = open(file_path, mode, os.O_NONBLOCK)
    if os.path.getsize(file_path) <= 0:
        f.write(csv_header)
    return f

def write_hist_value_callback():
    for f, v in zip(f_history_values, latest_reading_value):
	    write_value(f, latest_value_datetime, v)

def (type):
		
		
def write_latest_value(type):
i=0
j=0
for reading in sensor_readings_list:
    for record in record_types_list:
	    if record == 'latest':
		    with open_file_write_header(get_readings_parameters(reading, 'latest_file_path'), 'w', get_readings_parameters(reading, 'csv_header_readings')) as f_latest_value: 
    		    write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
		elif record == 'history':
		    with open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'w', get_readings_parameters(reading, 'csv_header_readings')) as f_latest_value:  
                write_value(f_latest_value, latest_value_datetime, latest_reading_value[i])
		j+=1
	i+=1
i=0
j=0
  
f_history_values =[]
for index, reading in enumerate(sensor_readings_list, start=0):
    f_history_values = open_file_write_header(get_readings_parameters(reading, 'history_file_path'), 'a', get_readings_parameters(reading, 'csv_header_reading'))


print "Ignoring first 2 sensor values to improve quality..."
for x in range(2):
    Adafruit_DHT.read_retry(sensor, pin)

print "Creating interval timer. This step takes almost 2 minutes on the Raspberry Pi..."
#create timer that is called every n seconds, without accumulating delays as when using sleep
scheduler = BackgroundScheduler()
scheduler.add_job(write_hist_value_callback, 'interval', seconds=sec_between_log_entries)
scheduler.start()
print "Started interval timer which will be called the first time in {0} seconds.".format(sec_between_log_entries);

try:
    while True:
	    latest_reading_value = get_sensor_readings(sensor, pin)
        latest_value_datetime = datetime.today()
        write_latest_value()
    time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

