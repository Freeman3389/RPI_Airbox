# How To Use This Project

## 1. Initialization your Raspberry Pi (a.k.a RPi)

**i) Download Raspbian Jessie from official site**
(https://www.raspberrypi.org/downloads/raspbian/)

**ii) Download ImageWriter**
(https://sourceforge.net/projects/win32diskimager/)

**iii) Write Raspbian Jessie image to MicroSD by ImageWriter**

**iv) Mount MicroSD /boot partition in Windows/MAC/Linux** 
Add following lines after the last line of *config.sts* to activate UART port of Raspberry Pi 3.
```
dtoverlay=pi3-disable-bt
enable_uart=1
```


**v) Connect USB-to-TTL cable to Raspberry.**
- Black(GND) => Pin 6
- White(UART Rx) => Pin 8
- Green(UART Tx) => Pin 10

**vi) Login Raspberry Pi by default account (pi/raspberry)**
```
$ sudo raspi-config
```
- Change User Password => Change password of default account, pi
- Hostname => Modify as what you want
- Localisation Options => Change Timezone => To where you live
- Interfacing Options => SSH, SPI, I2C, Serial should be enabled

**vii) Create a system account - rpisensor** 
input following command to create rpisensor for execution of RPi_Airbox programs.
```
$ sudo useradd -r rpisensor
$ sudo mkhomedir_helper rpisensor
$ sudo usermod -aG dialout,gpio,i2c,spi rpisensor
```

**viii) Modify /etc/sudoers**
```
$ sudo nano /etc/sudoers
```
Let rpisensor execute python script without any prompt of sudo password.
```
rpisensor       ALL=(ALL) NOPASSWD: /usr/bin/python
```

**ix) Install some necessary tools onto Raspberry Pi.**
```
$ sudo apt-get update
$ sudo apt-get install -y build-essential python-dev python-pip ntpdate git
$ sudo -HE pip install --upgrade pip
$ sudo -HE pip install psutil
```

**x) If you need to access Internet through proxy, please consider to configure following settings.**
```
- apt-get => /etc/apt/apt.conf.d
- git => sudo git config --global http.proxy [your proxy]
         sudo git config --global https.proxy [your proxy]
- pip => export https_proxy=[your proxy]
sudo -E pip install [module]
```

**xi) Get RPi_Airbox repository from Github**
```
$ cd /opt
$ sudo git clone https://github.com/Freeman3389/RPi_Airbox.git
```

**xii)  Check setting.json settings**
```
$ sudo nano /opt/RPi_Airbox/settings.json
```
Check settings of *global*, especially *sensor_location*
Check settings of each model. 
If you have the specific module in your RPi box, 
make sure the *status* set to *1* to let loader.py bring it up.

**xiii) Create monitor_web\sensor_values directory to store data**
```
$ sudo mkdir /opt/RPi_Airbox/monitor_web/sensor_values
```

**xiv) Sync time with NTP server (if possible)**
```
$ sudo systemctl stop ntp
$ sudo ntpdate [your NTP server]
```

**xv) Disable Bluetooth module for speeding up UART port**
```
sudo systemctl disable hciuart
```


## 2. Set up DHT22 temperature and humidity sensor (GPIO)
Before this part, you have to connect DHT22 sensor to your RPi correctly, 
and know what GPIO Pin that you connect to DHT22 data pin.

**i) Change to /opt/RPi_Airbox/dht22 directory**
```
& cd /opt/RPi_Airbox/dht22
```

**ii) Download DHT22 library from Github and install it.**
```
$ sudo git clone https://github.com/adafruit/Adafruit_Python_DHT.git
$ cd Adafruit_Python_DHT
$ sudo python setup.py install
```

After this, you can do a simple test by input *"examples/AdafruitDHT.py 2302 [GPIO Pin #]"*.
If you can see output like *"Temp=26.3*  *Humidity=44.1%"*, your DHT22 should work.

**iii) Check setting.json settings**
- Modify settings.json. The *gpio_pin* should base on your wiring
- Make sure *status* of *dht22* is *1*

## 3. Set up MQ2 smoke sensor (via ADC to GPIO)
Before this part, you have to connect MQ2 sensor to your RPi correctly, 
and know which ADC channel that you connect to MQ2 Analog pin.
(https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/)

**i) Make sure necessary python modules had been installed.**
```
$ sudo -HE pip install spidev
```

**ii) Check setting.json settings**
- *mq_channel* settings of *mq2* in settings.json
- Make sure *status* of "mq2" is *1*.

**iii) Input following command to check if MQ2 is working.**
```
$ sudo python /opt/RPi_Airbox/mq2/example.py
```
Wait 5 minutes if no error message.
If you can see the value in console, your MQ2 is ready to work.

## 4. Set up Plantower PMS3003 PMx sensor (UART)
**i) Check UART device settings**
Check possible serial port device name from output of command below.
```
$ dmesg | grep tty 
```
By default, it should be */dev/ttyAMA0* or */dev/ttyS0*.
**ii) Check setting.json settings**
Check *serial_device* of *pms3003* settings in settings.json and "status" should be "1".

## 5. Set up ublox Neo6m GPS receiver (UART to USB)
**i) Check USB device settings**
```
$ lsusb                             # confirm PL2302 connectivity
$ ls /dev/ttyUSB* 						      # Make sure correct device name of USB
$ sudo cat /dev/ttyUSB0					    # Make sure the connection of GPS module had been established
```
**ii) Install necessary packages**
```
$ sudo apt-get install -y gpsd gpsd-clients  # Install gpsd & client
```
**iii) Install necessary modules**
```
$ sudo nano /etc/default/gpsd				#Modify necessafy settings
```
Check and modify the following settings based on your environment
```
DEVICES="/dev/ttyUSB0"              # Depend on the USB device name
GPSD_OPTIONS="-n"
GPSD_SOCKET=”/var/run/gpsd.sock”
```
**iv) Fix Raspbian Jessie systemd service default settings**
```
$ sudo systemctl stop gpsd.socket
$ sudo systemctl disable gpsd.socket
$ sudo systemctl enable gpsd.socket
$ sudo systemctl start gpsd.socket
```
**v) Test gpsd**
```
$ sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock
$ cgps -s
or
$ gpsmon
```
If you always see 'NO FIX' in cgps, but gpsmon can get your location, 
try to fix this issue by the following website.
(http://wiki.dragino.com/index.php?title=Getting_GPS_to_work_on_Raspberry_Pi_3_Model_B)

**vi) Check setting.json settings**
Make sure *status* of *neo6m* is *1*.

## 6. Set up LCD1602 (I2C) screen
**i) Install necessary packages**
```
$ sudo apt-get install -y python-smbus i2c-tools
```
after wiring, use command below to check I2C address of LCD1602
```
$ i2cdetect -y 1
```
**ii) Check setting.json settings**
- Make sure *status* of *lcd1602* is *1*.
- Check *i2c_bus* and *i2c_address* settings in settings.json

## 7. Set up SH1106 OLED screen
Before this part, you have to connect SH1106 screen to your RPi correctly.
(https://luma-oled.readthedocs.io/en/latest/)
Because sh1106-upload.py will get the sensor values from the latest csv files from other sensors, 
it should not work before those csv files presented.

**i) Install necessary module**
```
$ sudo apt-get install -y i2c-tools python-smbus libfreetype6-dev libjpeg-dev
$ sudo -HE pip install --upgrade pip
$ sudo apt-get purge python-pip
$ sudo -HE pip install --upgrade luma.oled
```

After installed, input follow command to detect your SH1106 address. 
The last number in the command is the i2c port number.
  
```
$ i2cdetect -y 1
```

**ii) Base on the result of detection, modify SSH1106 settings in settings.json.**
- "i2c_port" => "1"  (Unless, your RPi is very old model, and you can try "0")
- "i2c_address" => "[SH1106 address]"
- "device_height" => "64" (By default, but you still have to check your specs)
- "status" => "1"

## 8. Set up snmp-passpersist
Because sh1106-upload.py will get the sensor values from the latest csv files from other sensors, it should not work before those csv files presented.
**Please DONT set its "status" to "1" in settings.json.**

**i) Install necessary module**
```
$ sudo -HE pip install snmp-passpersist
$ sudo apt-get install -y snmpd
```

**ii) modify /etc/snmp/snmpd.conf**
If you have no idea how to modify it, you can refer to the snmpd.conf inside snmp-passpersist directory.
However, you have to modify following settings of it according to your network.
```
rocommunity public  192.168.1.0/24 -V all
=>
rocommiuity [your ro community] [your NMS server] -V all
```
Add following line into the last of snmpd.conf
```
pass_persist .1.3.6.1.4.1.16813.1 /usr/bin/python -u /opt/RPi_Airbox/snmp-passpersist/snmp-passpersist-upload.py

```

**iii) modify *"sensor-readings-list"* array of *"snmp-passpersist"* settings in settings.json according to your sensors.**

**iv) Add system account - snmp to rpisensor group**
```
$ sudo usermod -aG snmp rpisensor
```

**v) Restart snmpd by following command**
```
$ sudo service snmpd restart
```
After restarted, check the status of snmpd
```
$ sudo service snmpd status
$ netstat -ln
$ tail -f /var/log/syslog | grep snmp
```

## 9. Set up Thingspeak upload module
**i) Check setting.json settings**
- Make sure *status* of *thingspeak* is *1*
- Modify *api_key* settings in settings.json
**2) Modify channel content if necessary**


## 10. Set up MQTT upload module
**i) install necessary module**
```
sudo -HE pip install paho-mqtt
```
**2) Check Module settings in settings.json**
- "status" => "1"
- "debug-enable" => "0"     # Not ready yet
- "client_id"               # Preserve for Node-Red MQTT, not ready yet.
- "username"                # Preserve for Node-Red MQTT, not ready yet.
- "passwd"                  # Preserve for Node-Red MQTT, not ready yet.


## 10. Set up Monitor Web module
Not ready yet

## 12. Set up automatical execution programs after reboot.

**i) Make sure the owner of "/opt/RPi_Airbox" is rpisensor**
```
$ sudo chown -R rpisensor:rpisensor /opt/RPi_Airbox
```

**ii) Try to bring all modules on by manually execute loader**
```
$ cd /opt/RPi_Airbox
$ /usr/bin/sudo /usr/bin/python /opt/RPi_Airbox/RPi_Airbox_loader.py
```
You should see the result like below if everything goes well.
```
Finished checking RPi_Aribox scripts
Loader summary: Enabled - 3 ; Disabled - 6 ; Running - 0 ; Loading - 3
Enabled Modules - sh1106, mq2, dht22
Disabled Modules - thingspeak, global, snmp-passpersist, pms3003, lcd1602, neo6m
Running Modules -
Loading Modules - sh1106, mq2, dht22
RPi_Airbox_loader.py execution time =    46.0970 Secs
```

**iii) Modify /etc/rc.local to let everything start after each reboot.**
```
$ sudo nano /etc/rc.local
```
Add these 3 lines below into rc.local before *"exit 0"*
```
/usr/bin/sudo /usr/bin/python /opt/RPi_Airbox/RPi_Airbox_loader.py >/dev/null 2>&1
/usr/bin/sudo ntpdate -s [your NTP server] >/dev/null 2>&1
```

**iv) Create a scheduled task to check all scripts are running every hour.**
```
$ sudo crontab -e
```
Add following 2 lines into crontab, and it will execute the RPi_Airbox_loader.py every hour at 30 minutes, 
also sync time with NTP on the hour.
```
30 * * * * /usr/bin/sudo /usr/bin/python /opt/RPi_Airbox/RPi_Airbox_loader.py >/dev/null 2>&1
0 * * * * /usr/bin/sudo ntpdate -s [your ntp server] >/dev/null 2>&1
```

## Done!
	
