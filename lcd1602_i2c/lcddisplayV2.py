import I2C_LCD_driver
import time,csv
mylcd = I2C_LCD_driver.lcd()
sensor = None
sensor_reading = None

def dht_reading(sensor):
    # Get DHT sensor readings from sensor_csv file
    sensor_location = 'living-room'
    sensor_csv = '/home/pi/projects/temp-and-humidity/sensor-values/'+sensor+'_'+sensor_location+'_latest_value.csv'
    with open(sensor_csv,'rb') as file:
        csvfile=csv.reader(file, delimiter=',')
        next(csvfile, None)
        for row in csvfile:
           sensor_reading=row[1]
    return sensor_reading

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


try:
    while True:
        mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"), 1, 1)
        mylcd.lcd_display_string("T:"+dht_reading('temperature')+"c", 2, 0)
        mylcd.lcd_display_string("H:"+dht_reading('humidity')+"%", 2, 9)
        time.sleep(1)

except KeyboardInterrupt:
    mylcd.lcd_clear()
    print ("User canceled, screen clear!!")

if __name__ == "__main__":
    main()