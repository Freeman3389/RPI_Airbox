import I2C_LCD_driver
import time,csv, sys, os
mylcd = I2C_LCD_driver.lcd()
sensor = None
sensor_reading = None
data_path = '/opt/RPi_Airbox/monitor_web/sensor-values/'

def dht_display(sensor):
    # Get DHT sensor readings from sensor_csv file
    sensor_location = 'living-room'
    sensor_csv = data_path+sensor+'_'+sensor_location+'_latest_value.csv'
    with open(sensor_csv,'rb') as file:
        csvfile=csv.reader(file, delimiter=',')
        next(csvfile, None)
        for row in csvfile:
           sensor_reading=row[1]
    return sensor_reading


def main():
    while True:
        try:
            mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"), 1, 1)
            mylcd.lcd_display_string("T:"+dht_reading('temperature')+"c", 2, 0)
            mylcd.lcd_display_string("H:"+dht_reading('humidity')+"%", 2, 9)
            time.sleep(1)

    except KeyboardInterrupt:
        mylcd.lcd_clear()
        print ("User canceled, screen clear!!")

    except IOError:
        mylcd.lcd_clear()
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"), 1, 1)
        mylcd.lcd_display_string("CANNOT Get data.", 2, 0)
        time.sleep(10)
        continue()

if __name__ == "__main__":
    main()
