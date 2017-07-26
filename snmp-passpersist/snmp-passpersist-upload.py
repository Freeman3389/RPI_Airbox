# !/usr/bin/python -u
# -*- coding:Utf-8 -*-
# Option -u is needed for communication with snmpd
# License: GPL 2.0
# Copyright 2017-2018 - Freeman Lee <freeman.lee@quantatw.com>
# Version 0.1.0 @ 2017.06.30

###########################################################################
#
# This file is for Raspberry Pi Sensor SNMP Pass_Persist
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################


import snmp_passpersist as snmp  # pip install snmp-passpersist
import csv
import syslog
import sys
import time
import errno
import platform
import os
import datetime
import json
import psutil  # pip install psutil
import Adafruit_DHT  # install Adafruit DHT Library

# Get settings from 'settings.json'
with open('/opt/RPi_Airbox/settings.json') as json_handle:
    configs = json.load(json_handle)
data_path = configs['global']['base_path'] + configs['global']['csv_path']
sensor_location = configs['global']['sensor_location']
update_interval = int(configs['snmp-passpersist']['update_interval'])
# General stuff
sensors = ['humidity', 'temperature', 'pm1-cf', 'pm10-cf', 'pm25-cf', 'pm1-at', 'pm10-at', 'pm25-at', 'latitude', 'longitude', 'altitude', 'GAS-LPG', 'CO', 'Smoke']
MAX_RETRY = 10				# Number of success retry in case of error
# Global vars
OID_BASE = ".1.3.6.1.4.1.16813.1"
pp = None

"""
Map of snmp_rpisensors MIB :

+--RpiStats(1)
   |
   +--RpiStatsHost(1)
      |
      +-- -R-- String    RpiStatsHostName(1)
      |        Textual Convention: DisplayString
      |        Size: 0..255
      +-- -R-- Gauge     RpiStatsHostCpuQty(2)
      +-- -R-- String    RpiStatsHostCpuClock(3)
      +-- -R-- String    RpiStatsHostUname(4)
      +-- -R-- Counter   RpiStatsHostDiskRead(5)     (Bytes)
      +-- -R-- Counter   RpiStatsHostDiskWrite(6)    (Bytes)
      |
      +--RpiStatsHostMem(7)
      |  |
      |  +-- -R-- Gauge     RpiStatsHostMemUsed(1)		(Bytes)
      |  +-- -R-- Gauge     RpiStatsHostMemFree(2)		(Bytes)
      |  +-- -R-- Gauge     RpiStatsHostMemUsage(3)		(Percentage*100, 0-10000)
      |
      +--RpiStatsHostMountPoints(8)
      |  |  Index: RpiStatsHostMountPointName
      |  |
      |  +-- -R-- String    RpiStatsHostMountPointName(1)
      |  |        Textual Convention: DisplayString
      |  |        Size: 0..255
      |  +-- -R-- Counter   RpiStatsHostMountPointFree(2)	  (Bytes)
      |  +-- -R-- Counter   RpiStatsHostMountPointUsage(3)	  (Percentage*100, 0-10000)
      |
      |
      +--RpiStatsHostNics(9)
      |  |  Index: RpiStatsHostNicName
      |  |
      |  +-- -R-- String    RpiStatsHostNicName(1)
      |  |        Textual Convention: DisplayString
      |  |        Size: 0..255
      |  +-- -R-- Counter   RpiStatsHostNicRx(2)		(Bytes)
      |  +-- -R-- Counter   RpiStatsHostNicTx(3)		(Bytes)
      |
      +--RpiStatsHostSensors(10)
      |  |  Index: RpiStatsHostSensorName
      |  |
      |  +-- -R-- String    RpiStatsHostSensorName(1)
      |  |        Textual Convention: DisplayString
      |  |        Size: 0..255
      |  +-- -R-- Gauge     RPiStatsHostSensorHumi1(2)		(Percentage*100: 0-1000)
      |  +-- -R-- Gauge     RpiStatsHostSensorTemp1(3)		(Degree C)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm1-cf(4)		(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm10-cf(5)	(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm25-sf(6)	(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm1-at(7)		(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm10-at(8)	(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorPm25-at(9)	(ug/m3)
      |  +-- -R-- Gauge     RpiStatsHostSensorLati(10)		(Degree)
      |  +-- -R-- Gauge     RpiStatsHostSensorLong(11)		(Degree)
      |  +-- -R-- Gauge     RpiStatsHostSensorAlti(12)		(Meter)
      |  +-- -R-- Gauge     RpiStatsHostSensorLPG(13)		(PPM * 10^6)
      |  +-- -R-- Gauge     RpiStatsHostSensorCO(14)		(PPM * 10^6)
      |  +-- -R-- Gauge     RpiStatsHostSensorSmoke(15)		(PPM * 10^6)
      |
      +-- -R-- Gauge     RpiStatsHostBootTime(11)
      +-- -R-- Gauge     RpiStatsHostCpuUsage(12)      (Percentage*100: 0-10000)


Shell command to walk through this tree :
	snmpwalk -v 2c -c netcomm localhost -m all -M/ .1.3.6.1.4.1.16813
"""


def get_reading_csv(sensor):
    """Get senson readings from latest csv files"""
    sensor_reading = None
    csv_path = data_path + sensor + '_' + sensor_location + '_latest_value.csv'
    with open(csv_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader)  # skip header of csv file
        for row in csvreader:
            sensor_reading = row[1]  # get second value
    return sensor_reading


def update_data():
    """Update snmp's data from psutil and sensor"""
    global pp
    global sensors
    # Load all stats once
    partitions = psutil.disk_partitions()
    nic_counters = psutil.net_io_counters(pernic=True)

    # Node info
    pp.add_str('1.1.0', platform.node())
    pp.add_gau('1.2.0', psutil.cpu_count())
    pp.add_str('1.3.0', psutil.cpu_freq())
    pp.add_str('1.4.0', platform.uname())
    pp.add_cnt_32bit('1.5.0', psutil.disk_io_counters().read_bytes)
    pp.add_cnt_32bit('1.6.0', psutil.disk_io_counters().write_bytes)
    pp.add_gau('1.11.0', datetime.datetime.fromtimestamp(
        psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))
    pp.add_gau('1.12.0', psutil.cpu_percent())

    # Memory info
    pp.add_gau('1.7.1.0', psutil.virtual_memory().used)
    pp.add_gau('1.7.2.0', psutil.virtual_memory().free)
    pp.add_gau('1.7.3.0', psutil.virtual_memory().percent)

    # Mount Point's Usage
    for part in partitions:
        oid = pp.encode(part.mountpoint)
        pp.add_str('1.8.1.' + oid, part.mountpoint)
        pp.add_gau('1.8.2.' + oid, psutil.disk_usage(part.mountpoint).free)
        pp.add_gau('1.8.3.' + oid, psutil.disk_usage(part.mountpoint).percent)

    # Network's IO
    for name in nic_counters.keys():
        oid = pp.encode(name)
        pp.add_str('1.9.1.' + oid, name)
        pp.add_cnt_32bit('1.9.2.' + oid, nic_counters[name].bytes_sent)
        pp.add_cnt_32bit('1.9.3.' + oid, nic_counters[name].bytes_recv)
    i = 2

    # Get each kind of readings from sensor latest value csv file
    i = 2
    for sensor in sensors:
        oid = pp.encode(sensor)
        pp.add_str('1.10.1.' + oid, sensor)
        if sensor == 'GAS-LPG' or sensor == 'CO' or sensor == 'Smoke':
            pp.add_str('1.10.' + str(i) + '.' + oid, str('{0:.6f}'.format(float(get_reading_csv(sensor))*100000)))
        else:
            pp.add_str('1.10.' + str(i) + '.' + oid, get_reading_csv(sensor))
        i += 1
    i = 0


def main():
    """Feed the snmp_RPi_Sensors MIB tree and start listening for snmp's passpersist."""
    global pp
    syslog.openlog(sys.argv[0], syslog.LOG_PID)

    retry_timestamp = int(time.time())
    retry_counter = MAX_RETRY
    while retry_counter > 0:
        try:
            syslog.syslog(syslog.LOG_INFO, "Starting RPi monitoring...")
            # Load helpers
            pp = snmp.PassPersist(OID_BASE)
            # Shouldn't return, except if updater thread has died)
            pp.start(update_data, update_interval)
        except KeyboardInterrupt:
            print "Exiting on user request."
            sys.exit(0)
        except IOError, ioer:
            if ioer.errno == errno.EPIPE:
                syslog.syslog(syslog.LOG_INFO,
                              "Snmpd had closed the pipe, exiting...")
                sys.exit(0)
            else:
                syslog.syslog(syslog.LOG_WARNING,
                              "Updater thread was died: IOError: %s" % (ioer))
        except Exception, e:
            syslog.syslog(syslog.LOG_WARNING, "Main thread was died: %s: %s" % (
                e.__class__.__name__, e))
        else:
            syslog.syslog(syslog.LOG_WARNING,
                          "Updater thread was died: %s" % (pp.error))
        syslog.syslog(syslog.LOG_WARNING, "Restarting monitoring in 15 sec...")
        time.sleep(15)

        # Errors frequency detection
        now = int(time.time())
        if (now - 3600) > retry_timestamp: 	# If the previous error is older than 1H
            retry_counter = MAX_RETRY			# Reset the counter
        else:
            retry_counter -= 1				# Else countdown
        retry_timestamp = now

    syslog.syslog(
        syslog.LOG_ERR, "Too many retry, abording... Please check if all the sensors are working !")
    sys.exit(1)


if __name__ == "__main__":
    main()
