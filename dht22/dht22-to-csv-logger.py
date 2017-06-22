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
sensor                       = Adafruit_DHT.AM2302 #DHT11/DHT22/AM2302
pin                          = 4
#csv files related parameters
sensor_location              = "living-room"
sensor_name                  = "DHT22"
sensor_reading_dict          = dict(zip(["temperatureC","humidity"],[0.0,0.0]))
base_path                    = "/opt/RPi_Airbox/monitor_web/sensor-values/"
hist_sensor_file_path        = base_path + sensor_name + "_" + sensor_location + "_log_" + datetime.date.today().strftime('%Y_%m') + ".csv"
latest_sensor_file_path      = base_path + sensor_name + "_" + sensor_location + "_latest_value.csv"
headers_sensor_readings      = ",".join([str(item) for item in sensor_reading_list])
csv_header_sensor            = "timestamp," + (",".join(sensor_reading_dict.keys())) + "\n"
csv_entry_format             = "{:%Y-%m-%d %H:%M:%S},{:0.1f}\n"
sec_between_log_entries      = 300
latest_value_datetime        = None

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
  write_value(f_hist_temp, latest_value_datetime, latest_temperature)
  write_value(f_hist_hum, latest_value_datetime, latest_humidity)

def write_latest_value():
  with open_file_write_header(latest_temperature_file_path, 'w', csv_header_temperature) as f_latest_value: 
    write_value(f_latest_value, latest_value_datetime, latest_temperature)
  with open_file_write_header(latest_humidity_file_path, 'w', csv_header_humidity) as f_latest_value:  
    write_value(f_latest_value, latest_value_datetime, latest_humidity)

f_hist_temp = open_file_write_header(hist_temperature_file_path, 'a', csv_header_temperature)
f_hist_hum  = open_file_write_header(hist_humidity_file_path, 'a', csv_header_humidity)

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
        sensor_readings=list(Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4))
		sensor_readings= ["%.2f" % member for member in sensor_readings]
        if hum is not None and temp is not None:
            latest_humidity, latest_temperature = hum, temp
            latest_value_datetime = datetime.today()
            write_latest_value()
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
  scheduler.shutdown()

