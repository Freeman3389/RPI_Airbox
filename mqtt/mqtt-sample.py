
import serial
import time
import threading
import os
import paho.mqtt.client as mqtt
from gps import *
from time import *
# Global variables intialization
gpsd = None

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
            gpsd.next()

class Setting:
    def __init__(self):
        #system general setting
        self.debug_enable=0 #Default:0, 0: debug disable , 1: debug enable
        self.plot_cnt=90 #Default:90,  the value count in plotter, if 10 seconds for 1 value, about 15 min.
        #self.mqtt_topic="LASS/#"   #REPLACE: to your sensor topic
        #self.mqtt_topic="LASS/Test/+"  #REPLACE: to your sensor topic, it do not subscribe device id's channel
        self.mqtt_topic="LASS/Test/#"  #Default: LASS/Test/+ , REPLACE: to your sensor topic, it do not subscribe device id's channel
        self.filter_par_type=2 #Default: 0, 0: no filer, 1: filter device_id, 2: filter ver_format
        self.device_id="" #Default: YOUR_DEVICE_NAME, REPLACE: to your device id
        self.ver_format=3 #Default 3,: filter parameter when filter_par_type=2
        self.kml_export_type=0 #Default:0, default kml export type. name = deviceid_localtime
        self.plot_enabled=0 #Default:0, 0: realtime plot not active, 1: active plot
        self.plot_save=1 #Default:1, 0: show plot realtime, 1:plot to file
        self.log_enabled=1 #Default:1, 0: not auto save receive data in log format, 1: auto save receive data in log format
        self.auto_monitor=0 #Default:1,0: not auto start monitor command, 1: auto start monitor commmand
        # plot, kml marker's color only apply to 1 sensor, this is the sensor id
        #0: battery level, 1: battery charging, 2: ground speed ( Km/hour )
        #10: dust sensor, 11: UIdust sensor, 12: sound sensor
        self.sensor_cur=0   #Default:0,REPLACE: to your interest current sensor

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")
    #topic="Sensors/#"
    client.subscribe(sEtting.mqtt_topic, qos=0)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #payload_hex = ''.join(format(str(x), '02x') for x in msg.payload)
    payload_str = str(msg.payload)
    console_str = datetime.datetime.now().strftime("%X") + "|" +msg.topic+ "|" +  payload_str[1:]
    if sEtting.debug_enable:
        print console_str

    (sensor_data,device) = dEvices.add(str(payload_str[1:]))
    if sensor_data:
        if sEtting.log_enabled:
            global data_log_file
            if data_log_file==None:
                data_log_file = open("lass_data_" + datetime.datetime.now().strftime("%Y%m%d") + ".log", 'w+')
            data_log_file.write(console_str + "\n")

            global data_file
            if data_file==None:
                data_file = open("lass_data_" + datetime.datetime.now().strftime("%Y%m%d") + ".raw", 'w+')
            data_file.write(sensor_data.raw + "\n")

        if sEtting.plot_enabled:
            sensorPlot.plot(1)
        (distance,is_move) = device.is_move()
        if is_move:
            print "%s is moving" %(device.id)
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("180.76.179.148", 1883, 60)
#MQTT服务器地址，端口，KeepAlive时间

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

if __name__ == '__main__':
    gpsp = GpsPoller() # create the thread
    try:
        gpsp.start() # start it up
        while True:
            #It may take a second or two to get good data
            #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc
 
            os.system('clear')
 
            print
            print ' GPS reading'
            print '----------------------------------------'
            print 'latitude    ' , gpsd.fix.latitude
            print 'longitude   ' , gpsd.fix.longitude
            print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
            print 'altitude (m)' , gpsd.fix.altitude
            print 'eps         ' , gpsd.fix.eps
            print 'epx         ' , gpsd.fix.epx
            print 'epv         ' , gpsd.fix.epv
            print 'ept         ' , gpsd.fix.ept
            print 'speed (m/s) ' , gpsd.fix.speed
            print 'climb       ' , gpsd.fix.climb
            print 'track       ' , gpsd.fix.track
            print 'mode        ' , gpsd.fix.mode
            print
            print 'sats        ' , gpsd.satellites
 
            time.sleep(5) #set to whatever
 
    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing