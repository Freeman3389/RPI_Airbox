
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

class SensorData:
    def __init__(self,payload):
        #example payload
        #V0.1-V0.2
        #|device_id=LASS-Wuulong|time=2474079|device=LinkItONE|values=14|gps=$GPGGA,103106.000,2448.0291,N,12059.5732,E,1,4,5.89,29.9,M,15.0,M,,*63
        #V0.3
        #08:01:25|LASS/Test/EXAMPLE_APP b'|app=EXAMPLE_APP|device_id=LASS-Wuulong|tick=11569371|date=7/7/15|time=15:18:32|device=LinkItONE|values=0,100,1|gps=$GPGGA,151832.001,2446.5223,N,12050.1608,E,0,0,,-0.0,M,14.9,M,,*64\r'

        self.raw = payload
        self.valid=0 # only use data when valid=1
        self.localtime=datetime.datetime.now()

        # parameters valid after data_processing
        self.value_dict={} # value is string type
        self.datatime=0
        self.app=""
        self.gps_x=0.0
        self.gps_y=0.0
        self.gps_z=0.0
        self.gps_lon=0.0
        self.gps_lat=0.0
        self.gps_alt=0.0
        self.sensor_types=[]
        self.sensor_values=[]
        self.ver_format=0 #int type
        self.ver_app="0.0"   #string type
        self.data_process()
        self.check_valid()
        self.filter_out=False #False: user need this data, True: user don't need this data for now

    def desc(self):
        print "datatime=%s,gps=%f,%f,%f, filter_out=%s, values=%s" % (str(self.datatime),self.gps_lat,self.gps_lon,self.gps_alt, str(self.filter_out),str(self.get_values("")))
        #print("datatime=" + str(self.datatime) + ", filter_out=" + str(self.filter_out) + ",values=" + str(self.get_values("")) )
    #although csv head is the same for every record, it still good to be allocate here.
    def get_csvhead(self):
        #|ver_format=1|app=HELLO_APP|ver_app=0.6|device_id=LASS-Hello|tick=13072946|date=1/8/15|time=16:0:10|device=LinkItONE
#ver_format,app,ver_app,device_id,tick,datetime,device,value0,gps_x,gps_y,gps_z
        csv_head = "ver_format,app,ver_app,device_id,tick,datetime,device"
        csv_head = csv_head + ",gps_lat,gps_lon,gps_alt"
        for type in self.sensor_types:
            csv_head = csv_head +","+type
        if sEtting.debug_enable:
            print "csv_head %s" % csv_head
        return csv_head

    def get_csv(self):
#b'|app=EXAMPLE_APP|device_id=LASS-Example|tick=49484274|date=15/7/15|time=12:15:18|device=LinkItONE|values=47.00,100.00,1.00,856.27,544.52|gps=$GPGGA,121518.000,2447.9863,N,12059.5843,E,1,8,1.53,40.2,M,15.0,M,,*6B\r'
        ret_str = ""
        try:
            ret_str = self.value_dict["ver_format"] + "," + self.app + "," + self.value_dict["device_id"] + "," + self.value_dict["ver_app"] + "," + self.value_dict["tick"] + "," + self.value_dict["date"] + " " + self.value_dict["time"]+ "," + self.value_dict["device"]
            ret_str = ret_str + "," + str(self.gps_lat) + "," + str(self.gps_lon) + "," + str(self.gps_alt)
            for data in self.sensor_values:
                ret_str = ret_str + "," + data
            if sEtting.debug_enable:
                print "csv_str %s" % ret_str
        except :
            print( "[GET_CSV] Oops!  Export get un-expcected data, maybe it's old version's data")
        return ret_str

    def get_jsonhead(self):
        head = 'lass_callback({"type":"FeatureCollection","metadata":{"generated":1395197681000,"url":"https://github.com/LinkItONEDevGroup/LASS","title":"LASS Sensors data","status":200,"api":"0.7.1","count":3},"features":['
        return head

    def get_json(self):
#{"type":"Feature","properties":{"data_d":7.0,"ver_format":2,"fmt_opt":0,"app":"EXAMPLE_APP2","ver_app":"0.7.1","device_id":"LASS-DUST-LJ","tick":160839412,"date":"2015-10-15","time":"06:26:14","device":"LinkItONE","data-0":16100.00,"data-1":100.00,"data-2":1.00,"data-3":0.00,"data-D":9.00,"gps-lat":25.023487,"gps-lon":121.370950,"gps-fix":0,"gps-num":0,"gps-alt":13},"geometry":{"type":"Point","coordinates":[121.370950,25.023487,8.7]},"id":""}
        ret_str = ""
        try:
            str_head = '{"type":"Feature","properties":{'
            str_fmt1 = '"ver_format":%s,"fmt_opt":%s,"app":"%s","ver_app":"%s","device_id":"%s","tick":%s,"date":"%s","time":"%s","device":"%s","gps_lat":%s,"gps_lon":%s,"gps_fix":%s,"gps_num":%s,"gps_alt":%s'
            str_base = str_fmt1 % (self.value_dict["ver_format"],self.value_dict["fmt_opt"],self.value_dict["app"],self.value_dict["ver_app"],self.value_dict["device_id"],self.value_dict["tick"],self.value_dict["date"],self.value_dict["time"],self.value_dict["device"],self.gps_lat,self.gps_lon,self.value_dict["gps_fix"],self.value_dict["gps_num"],self.gps_alt)
            str_fmt2 = '%s%s,%s},"geometry":{"type":"Point","coordinates":[%s,%s,%s]}'
            ret_str = str_fmt2 % (str_head,str_base,self.get_values_str("json"), self.gps_lon, self.gps_lat, self.gps_alt)
            if sEtting.debug_enable:
                print "json_str %s" % ret_str
        except :
            print( "[GET_JSON] Oops!  Export get un-expcected data, maybe it's old version's data")
        return ret_str

    def get_jsontail(self):
        #|ver_format=1|app=HELLO_APP|ver_app=0.6|device_id=LASS-Hello|tick=13072946|date=1/8/15|time=16:0:10|device=LinkItONE
#ver_format,app,ver_app,device_id,tick,datetime,device,value0,gps_x,gps_y,gps_z
        tail = '],"bbox":[-179.463,-60.7674,-2.9,178.4321,67.0311,609.13]});'
        return tail

    #parse the data and form the related variables.
    def data_process(self):
        global datetime_format_def
        if sEtting.debug_enable:
            print("[SensorData] raw=" + self.raw)
        cols=self.raw.split("|")
        for col in cols:
            if sEtting.debug_enable:
                print("col:" + col)
            pars = col.split("=")
            if len(pars)>=2:
                self.value_dict[pars[0]] = pars[1]
        #setup values
        try:
            self.parse_ver()
            if self.ver_app == "0.6.6":
                datetime_format_def = '%d/%m/%y %H:%M:%S'
            elif self.ver_app == "0.7.0":
                datetime_format_def = '%Y-%m-%d %H:%M:%S'
            else:
                datetime_format_def = '%Y-%m-%d %H:%M:%S'
            sEtting.device_id = self.value_dict["device_id"]
            self.parse_gps()
            self.parse_datatime()
            self.parse_app()
            #self.app = self.value_dict["app"]
            if self.ver_app in ["0.6.6" "0.7.0"]:
                self.parse_values()
            if self.ver_format==3:
                self.parse_data()
                pass
            self.valid=1
        except:
            print( "[DATA_PROCESS] Oops!  Data parser get un-expcected data when data_process")
        #self.gps_x = 24.780495 + float(self.value_dict["values"])/10000
        #self.gps_y = 120.979692 + float(self.value_dict["values"])/10000

    def parse_gps(self):
        try:
            if self.ver_app == "0.6.6":
                gps_str = self.value_dict["gps"]
                gps_cols=gps_str.split(",")
                y = float(gps_cols[4])/100
                x = float(gps_cols[2])/100
                z = float(gps_cols[9])

                y_m = (y -int(y))/60*100*100
                y_s = (y_m -int(y_m))*100

                x_m = (x -int(x))/60*100*100
                x_s = (x_m -int(x_m))*100

                self.gps_x = int(x) + float(int(x_m))/100 + float(x_s)/10000
                self.gps_y = int(y) + float(int(y_m))/100 + float(y_s)/10000
                self.gps_z = z
            elif self.ver_app == "0.7.0":
                gps_loc = self.value_dict["gps-loc"].replace("type", "\"type\"").replace("coordinates", "\"coordinates\"")
                gps_fix = self.value_dict["gps-fix"]
                gps_num = self.value_dict["gps-num"]
                gps_alt = self.value_dict["gps-alt"]
                gps_coor = list(json.loads(gps_loc)["coordinates"])

                r = 6371000 + float(gps_alt)
                self.gps_x = r*math.cos(float(gps_coor[0]))*math.cos(float(gps_coor[1]))
                self.gps_y = r*math.cos(float(gps_coor[0]))*math.sin(float(gps_coor[1]))
                self.gps_z = r*math.sin(float(gps_coor[0]))
            else:
                gps_lat = self.value_dict["gps_lat"]
                gps_lon = self.value_dict["gps_lon"]
                gps_alt = self.value_dict["gps_alt"]
                if not bool(re.search(r'\d', gps_alt)): gps_alt=0
                #gps_fix = self.value_dict["gps_fix"]
                #gps_num = self.value_dict["gps_num"]

                ''' transform from (lat,lon,alt) to (x,y,z), not use currently
                #r = 6378137.0 + float(gps_alt)
                #self.gps_x = r*math.cos(float(gps_lat))*math.cos(float(gps_lon))
                #self.gps_y = r*math.cos(float(gps_lat))*math.sin(float(gps_lon))
                #self.gps_z = r*math.sin(float(gps_lat))
                '''

                self.gps_lat = self.gps_to_map(float(gps_lat))
                self.gps_lon = self.gps_to_map(float(gps_lon))
                self.gps_alt = self.gps_to_map(float(gps_alt))

            if sEtting.debug_enable:
                print("[parse_gps] gps_lat=" + str(self.gps_lat) + ",gps_lon=" + str(self.gps_lon)+ ",gps_alt=" + str(self.gps_alt))
        except:
            print("[PARSE_GPS] Oops!  Data parser get un-expcected data when parse_gps")
            print "raw data is: %s" % (self.raw)

    def parse_datatime(self):
        date_str = self.value_dict["date"]
        time_str = self.value_dict["time"]
        self.datatime = datetime.datetime.strptime( date_str + " " + time_str, datetime_format_def)

    def parse_app(self):
        self.app = self.value_dict["app"]

    def parse_values(self):
        self.sensor_values = self.value_dict["values"].split(",")

    def parse_data(self):
        data_string = self.get_values_str()
        data_cols = data_string.split(",")
        for col in data_cols:
            pair = col.split("=")
            if len(pair) >= 2:
                self.sensor_types.append(pair[0])
                self.sensor_values.append(pair[1])
        if sEtting.debug_enable:
            print '[parse_data sensor_types] [%s]' % ', '.join(map(str, self.sensor_types))
            print '[parse_data sensor_values] [%s]' % ', '.join(map(str, self.sensor_values))

    def parse_ver(self):
        try:
            self.ver_format=int(self.value_dict["ver_format"])
            self.ver_app = self.value_dict["ver_app"]
        except :
            pass

    #check if data valid and apply filter
    def check_valid(self):
        self.valid=0
        try:
            if sEtting.filter_par_type==1:
                if self.value_dict["device_id"]==sEtting.device_id:
                    self.valid=1
                else:
                    self.valid=0
            if sEtting.filter_par_type==2:
                if self.value_dict["ver_format"]==str(sEtting.ver_format) and self.value_dict["device_id"]:
                    self.valid=1
                else:
                    self.valid=0
        except :
            print ("Check_valid excption")
    #transfer gps value to google map format
    def gps_to_map(self,x):
        x_m = (x -int(x))/60*100*100
        x_s = (x_m -int(x_m))*100
        gps_x = int(x) + float(int(x_m))/100 + float(x_s)/10000
        return gps_x

    def get_values_str(self,output_type=""): # currently return "" if not valid. The return type is string
        values=""
        if self.valid!=1:
            return values

        sensors_cnt=0
        if self.ver_format ==3:
            for key in self.value_dict.keys():
                if key.startswith("s_"):
                    if sensors_cnt==0:
                        if output_type=="json":
                            values = '"' + key + '"' + ":" + self.value_dict[key]
                        else:
                            values = key + "=" + self.value_dict[key]
                    else:
                        if output_type=="json":
                            values = values + "," + '"' + key + '"' + ":" + self.value_dict[key]
                        else:
                            values = values + "," + key + "=" + self.value_dict[key]

                    sensors_cnt=sensors_cnt+1
        else:
            print ("ver_format:" + str(self.ver_format))

        return values
    def get_values(self,output_type=""):
        #default, return all values as list
        #values=self.value_dict["values"].split(",")
        values = self.get_values_str()
        return values


def init_config():
    global sEtting
    global dEvices
    global sensorPlot
    global aNalyzePar

    sEtting = Setting()
    dEvices = Devices()
    sensorPlot = SensorPlot()
    aNalyzePar = AnalyzePar()

def main():
    global cLient
    init_config()

    print("----- LASS V" + str(VERSION) + " -----")
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', default=None, help="Get current LASS.PY Version.")
    parser.add_argument('--testtopic', action='store_true', default=None, help="Test through the Topic: LASS/Test/+."
                                                               "\n device_id=LASS-Example")
    parser.add_argument('--lasscmd',action='store_true', default=None, help="LASS commandline interface.")
    parser.add_argument('--testdev',action='store_true', default=None, help="Run offline unit test.")
    args = parser.parse_args()

    if(args.version is not None):
        print("----- LASS.PY V" + str(VERSION) + " -----")

    if(len(sys.argv) == 1) or (args.testtopic is not None):
        #sEtting.auto_monitor = 1
        #fAker = FakeDataGenerator()
        cLient = mqtt.Client()
        cLient.on_connect = on_connect
        cLient.on_message = on_message
        cLient.loop_start
        #client.connect("gpssensor.ddns.net", 1883, 60)
        #client.loop_forever()
        LassCli().cmdloop()

    if args.lasscmd is not None:
        sEtting.auto_monitor = 0
        #fAker = FakeDataGenerator()
        cLient = mqtt.Client()
        cLient.on_connect = on_connect
        cLient.on_message = on_message
        cLient.loop_start
        #client.connect("gpssensor.ddns.net", 1883, 60)
        #client.loop_forever()
        LassCli().cmdloop()


    if args.testdev is not None:
        if VERSION == "0.7.5":
            ##APP_VERSION == "0.7.5" ver_format=3
            test_log = "LASS/Test/PM25 |ver_format=3|fmt_opt=0|app=PM25|ver_app=0.7.5|device_id=FT1_003|" \
                       "tick=5447049|date=2015-10-18|time=06:26:25|device=LinkItONE|" \
                       "s_0=459.00|s_1=66.00|s_2=1.00|s_3=0.00|s_d0=33.00|s_t0=22.60|s_h0=83.50|" \
                       "gps_lat=25.025452|gps_lon=121.371092|gps_fix=1|gps_num=9|gps_alt=3"
        elif VERSION == "0.7.0":
            test_log = "LASS/Test/MAPS |ver_format=1|fmt_opt=0|app=MAPS|ver_app=0.7.0|device_id=LASS-MAPS-LJ|" \
                    "tick=421323065|date=2015-10-10|time=06:54:42|device=LinkItONE|" \
                    "values=37249.00,100.00,1.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,1007.83,26.70,81.20,6.00,0.00,0.00,0.00,0.00,0.00,0.00|" \
                    "data-0=37249.00|data-1=100.00|data-2=1.00|data-3=0.00|data-B=1007.83|data-T=26.70|data-H=81.20|data-L=6.00|" \
                    "gps-loc={ type:\"Point\",  coordinates: [25.024463 , 121.368752 ] }|gps-fix=1|gps-num=6|gps-alt=3"
        elif VERSION == "0.6.6":
            test_log = "LASS/Test/MAPS |ver_format=1|fmt_opt=0|app=MAPS|ver_app=0.6.6|device_id=LASS-MAPS-LJ|" \
                   "tick=71787795|date=1/10/15|time=0:52:48|device=LinkItONE|" \
                   "values=6397.00,100.00,1.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,1010.88,33.00,99.90,119.00,0.00,0.00,0.00,0.00,0.00,0.00|" \
                   "gps=$GPGGA,005248.009,3024.2268,S,13818.7933,E,0,0,,-2001.4,M,12.7,M,,*44"
        elif VERSION == "0.7.1":
            test_log = "LASS/Test/MAPS |ver_format=2|fmt_opt=0|app=MAPS|ver_app=0.7.1|device_id=LASS-MAPS-LJ|" \
                   "tick=8521980|date=2015-10-19|time=06:29:41|device=LinkItONE|" \
                   "data-0=679.00|data-1=100.00|data-2=1.00|data-3=0.00|data-B=1001.64|data-T=26.90|data-H=72.70|data-L=24.00|" \
                   "gps-lat=25.040351|gps-lon=121.387630|gps-fix=0|gps-num=0|gps-alt=1"
        else:
            test_log = ""
            print "Not support this version: %s " % (VERSION)
        
        if test_log:
            dEvices.add(test_log)

if __name__ == "__main__":
    main()
    gpsp = GpsPoller() # create the thread


if __name__ == '__main__':
    
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