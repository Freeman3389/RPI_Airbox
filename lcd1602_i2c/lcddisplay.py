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

try:
    while True:
        mylcd.lcd_display_string(time.strftime("%m/%d %H:%M:%S"), 1, 1)
        mylcd.lcd_display_string("T:"+dht_reading('temperature')+"c", 2, 0)
        mylcd.lcd_display_string("H:"+dht_reading('humidity')+"%", 2, 9)
        time.sleep(1)

except KeyboardInterrupt:
    mylcd.lcd_clear()
    print ("User canceled, screen clear!!")
