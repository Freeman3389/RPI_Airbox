#!/usr/bin/python -u
# -*- coding:Utf-8 -*-
# Option -u is needed for communication with snmpd

# Copyright 2017-2018 - Freeman Lee <freeman.lee@quantatw.com>

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


import snmp_passpersist as snmp		#pip install snmp-passpersist
import csv
import syslog, sys, time, errno, platform, os, datetime
import psutil			        #pip install psutil
import Adafruit_DHT			#install Adafruit DHT Library
#import pdb

# General stuff
POOLING_INTERVAL=60			# Update timer, in second
MAX_RETRY=10				# Number of success retry in case of error
OID_BASE=".1.3.6.1.4.1.16813.1"

# Global vars
pp=None
sensors=['humidity','temperature']	#Define GPIO Sensors
dht_pin=4				#Define DHT sensor GPIO#

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
      |
      +-- -R-- Gauge     RpiStatsHostBootTime(11)       
      +-- -R-- Gauge     RpiStatsHostCpuUsage(12)      (Percentage*100: 0-10000) 


Shell command to walk through this tree :
	snmpwalk -v 2c -c netcomm localhost -m all -M/ .1.3.6.1.4.1.16813
"""

def adafruit_dht(dht_pin):
    #update snmp data from Adafruit DHT sensor
    (humidity, temperature) = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, dht_pin)
    if humidity is not None and temperature is not None:
        return (humidity, temperature)
    else:
        return ('Failed to get reading. Try again!')    

#def dht_reading(sensor):
#    sensor_location = 'QRDC-QMS-ServerRoom'
#    sensor_csv = '/home/pi/projects/temp-and-humidity/sensor-values/'+sensor+'_'+sensor_location+'_latest_value.csv'
#    with open(sensor_csv,'rb') as file:
#        csvfile=csv.reader(file, delimiter=',')
#        next(csvfile, None)
#        for row in csvfile:
#           sensor_reading=row[1]
#    return sensor_reading

def update_data():
    """Update snmp's data from psutil and sensor"""
    global pp
    global dht_pin
    global sensors
    # Load all stats once
    partitions=psutil.disk_partitions()
    nic_counters=psutil.net_io_counters(pernic=True)
    #dht_readings=adafruit_dht(dht_pin)

    # Node info
    pp.add_str('1.1.0',platform.node())
    pp.add_gau('1.2.0',psutil.cpu_count())
    pp.add_str('1.3.0',psutil.cpu_freq())
    pp.add_str('1.4.0',platform.uname())
    pp.add_cnt_32bit('1.5.0',psutil.disk_io_counters().read_bytes)
    pp.add_cnt_32bit('1.6.0',psutil.disk_io_counters().write_bytes)
    pp.add_gau('1.11.0',datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))
    pp.add_gau('1.12.0',psutil.cpu_percent())
    #pdb.set_trace()

    # Memory info
    pp.add_gau('1.7.1.0',psutil.virtual_memory().used)
    pp.add_gau('1.7.2.0',psutil.virtual_memory().free)
    pp.add_gau('1.7.3.0',psutil.virtual_memory().percent)
    #pdb.set_trace()

    # Mount Point's Usage
    for part in partitions:
        #pdb.set_trace()
        oid=pp.encode(part.mountpoint)
        pp.add_str('1.8.1.'+oid,part.mountpoint)
        pp.add_gau('1.8.2.'+oid,psutil.disk_usage(part.mountpoint).free)
        pp.add_gau('1.8.3.'+oid,psutil.disk_usage(part.mountpoint).percent)

    # Network's IO
    for name in nic_counters.keys():
        oid=pp.encode(name)
        pp.add_str('1.9.1.'+oid,name)
        pp.add_cnt_32bit('1.9.2.'+oid,nic_counters[name].bytes_sent)
        pp.add_cnt_32bit('1.9.3.'+oid,nic_counters[name].bytes_recv)
        #pdb.set_trace()


    # GPIO Sensors
    for sensor in sensors:
        oid=pp.encode(sensor)
        pp.add_str('1.10.1.'+oid,sensor)
        if sensor == 'humidity':
            pp.add_gau('1.10.2.'+oid,'{0:0.1f}'.format(adafruit_dht(dht_pin)[0]))
        if sensor == 'temperature':
            pp.add_gau('1.10.3.'+oid,'{0:0.1f}'.format(adafruit_dht(dht_pin)[1]))
#        pdb.set_trace()

    # Get Reading of GPIO Sensors from csv file
#    for sensor in sensors:
#        oid=pp.encode(sensor)
#        pp.add_str('1.10.1.'+oid,sensor)
#        if sensor == 'humidity':
#            pp.add_gau('1.10.2.'+oid,dht_reading(sensor))
#        elif sensor == 'temperature':
#            pp.add_gau('1.10.3.'+oid,dht_reading(sensor))
        #pdb.set_trace()

def main():
    #Feed the snmp_RPi_Sensors MIB tree and start listening for snmp's passpersist
    global pp
    syslog.openlog(sys.argv[0],syslog.LOG_PID)
	
    retry_timestamp=int(time.time())
    retry_counter=MAX_RETRY
    while retry_counter>0:
        try:
            syslog.syslog(syslog.LOG_INFO,"Starting RPi monitoring...")
            # Load helpers
            pp=snmp.PassPersist(OID_BASE)
            #pdb.set_trace()
            pp.start(update_data,POOLING_INTERVAL) # Shouldn't return, except if updater thread has died)
            #pdb.set_trace()
        except KeyboardInterrupt:
            print "Exiting on user request."
            sys.exit(0)
        except IOError, e:
            if e.errno == errno.EPIPE:
                syslog.syslog(syslog.LOG_INFO,"Snmpd had closed the pipe, exiting...")
                sys.exit(0)
            else:
                syslog.syslog(syslog.LOG_WARNING,"Updater thread was died: IOError: %s" % (e))
        except Exception, e:
#            pdb.set_trace()
            syslog.syslog(syslog.LOG_WARNING,"Main thread was died: %s: %s" % (e.__class__.__name__, e))
        else:
            syslog.syslog(syslog.LOG_WARNING,"Updater thread was died: %s" % (pp.error))
        syslog.syslog(syslog.LOG_WARNING,"Restarting monitoring in 15 sec...")
        time.sleep(15)

        # Errors frequency detection
        now=int(time.time())
        if (now - 3600) > retry_timestamp: 	# If the previous error is older than 1H
            retry_counter=MAX_RETRY			# Reset the counter
        else:
            retry_counter-=1				# Else countdown
        retry_timestamp=now

    syslog.syslog(syslog.LOG_ERR,"Too many retry, abording... Please check if xen is running !")
    sys.exit(1)

if __name__ == "__main__":
    main()
