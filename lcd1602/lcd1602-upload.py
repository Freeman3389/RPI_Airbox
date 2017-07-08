"""This script will get DHT22 sensor readings, and write to csv files."""
# !/usr/bin/python
# -*- coding: utf-8 -*-
# Originally written by 
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.06.30
# License: GPL 2.0

import I2C_LCD_driver
import time, csv, sys, os, syslog, json

# Get settings from '../settings.json'
with open('/opt/RPi_Airbox/settings.json') as json_handle:
    configs = json.load(json_handle)
data_path = configs['global']['base_path'] + configs['global']['csv_path']
update_interval = int(configs['lcd1602']['update_interval'])
# initial variables
mylcd = I2C_LCD_driver.lcd()
syslog.openlog(sys.argv[0], syslog.LOG_PID)
latest_reading_values = []


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
    while True:
        try:
            """Display date, time, temperature, humidity on LCD"""
            for idx in range(9):
                mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"),1 ,1)
                mylcd.lcd_display_string("T:" + get_reading_csv('temperature')+"c",2 ,0)
                mylcd.lcd_display_string("H:" + get_reading_csv('humidity')+"%",2 ,9)
                time.sleep(1)
            mylcd.lcd_clear()
            """Display PMx values on LCD"""
            mylcd.lcd_display_string("PM1.0:" + get_reading_csv('pm1-at'),1 ,0)
            mylcd.lcd_display_string("PM2.5:" + get_reading_csv('pm25-at'),1 ,9)
            mylcd.lcd_display_string("PM10:" + get_reading_csv('pm25-at'),2 ,0)
            time.sleep(update_interval)
            mylcd.lcd_clear()
            """Display GPS Latitude and Longitude on LCD"""
            mylcd.lcd_display_string("Lat: N" + get_reading_csv('latitude'),1 ,0)
            mylcd.lcd_display_string("Lon: E" + get_reading_csv('longitude'),2, 0)
            time.sleep(update_interval)
            mylcd.lcd_clear()          
    except KeyboardInterrupt:
        mylcd.lcd_clear()
        print ("User canceled, screen clear!!")

    except IOError:
        mylcd.lcd_clear()
        syslog.syslog(syslog.LOG_WARNING, "I/O error({0}): {1}".format(e.errno, e.strerror)
        mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"), 1, 1)
        mylcd.lcd_display_string("CANNOT Get data.", 2, 0)
        time.sleep(10)
        continue

if __name__ == "__main__":
    main()
