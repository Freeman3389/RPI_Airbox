#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014-17 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK
# Re-written by Freeman Lee
# Version 0.1.0 @ 2017.07.15
import os
import time
import csv
import sys
import syslog
import json
from luma.oled.device import sh1106
from luma.core.render import canvas
from luma.core.virtual import viewport
from PIL import ImageFont

# Get settings from '../settings.json'
with open('/opt/RPi_Airbox/settings.json') as json_handle:
    configs = json.load(json_handle)
data_path = configs['global']['base_path'] + configs['global']['csv_path']
sensor_location = configs['global']['sensor_location']
update_interval = int(configs['sh1106']['update_interval'])
# initial variables
syslog.openlog(sys.argv[0], syslog.LOG_PID)
latest_reading_values = []
device = sh1106(port=1, address=0x3C)


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
        # use custom font
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    'luma.oled/examples/fonts', 'C&C Red Alert [INET].ttf'))
        font2 = ImageFont.truetype(font_path, 16)

        virtual = viewport(device, width=device.width, height=120)
    
        with canvas(virtual) as draw:
            draw.text((0, 0), time.strftime("%Y/%m/%d %H:%M:%S"), font=font2, fill="white")
            draw.text((0, 16), "Temp: " + str(get_reading_csv('temperature')) + " c", font=font2, fill="white")
            draw.text((0, 32), "Humi: " + str(get_reading_csv('humidity')) + " %", font=font2, fill="white")
            draw.text((0, 48), "Smoke: " + str(get_reading_csv('Smoke')) + " ppm", font=font2, fill="white")
            draw.text((0, 64), "CO: " + str(get_reading_csv('CO')) + " ppm", font=font2, fill="white")
            draw.text((0, 80), "LPG: " + str(get_reading_csv('GAS-LPG')) + " ppm", font=font2, fill="white")
     
        # update the viewport one position below, causing a refresh,
        # giving a rolling up scroll effect when done repeatedly
        for y in range(32):
            virtual.set_position((0, y))
            time.sleep(0.1)
        time.sleep(1)   
        for y in range(32, 0, -1):
            virtual.set_position((0, y))
            time.sleep(0.1)
            
        time.sleep(update_interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
