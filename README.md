# How To Use This Project

## 1. Initialization your Raspberry Pi (a.k.a RPi)

**i) Download Raspbian Jessie from official site**
(https://www.raspberrypi.org/downloads/raspbian/)

**ii) Download ImageWriter**
(https://sourceforge.net/projects/win32diskimager/)

**iii) Write Raspbian Jessie image to MicroSD by ImageWriter**

**iv) Mount MicroSD /boot partition in Windows/MAC/Linux and add *"dtoverlay=pi3-disable-bt"* after the last line of *config.txt* 
to activate UART port of Raspberry Pi 3.**

**v) Connect USB-to-TTL cable to Raspberry. *Black(GND) => Pin 6, White(UART Rx) => Pin 8, Green(UART Tx) => Pin 10* **

**vi) Login Raspberry Pi by default account (pi/raspberry), then input *"sudo raspi-config"* to do basic setup.**
  - Change User Password => Change password of default account, pi
  - Hostname => Modify as what you want
  - Localisation Options => Change Timezone => To where you live
  - Interfacing Options => SSH, SPI, I2C, Serial should be enabled

**vii) After reboot, input following command to create a system account - rpisensor for execution of RPi_Airbox programs.**
  ```
  $ sudo useradd -r rpisensor
  $ sudo mkhomedir_helper rpisensor
  $ sudo usermod -aG dialout,gpio,i2c,spi rpisensor
  ```

**viii) input *"sudo nano /etc/sudoers”* to let rpisensor execute python script without any prompt of sudo password.**
  ```
  rpisensor       ALL=(ALL) NOPASSWD: /usr/bin/python
  ```

**ix) Install some necessary tools onto Raspberry Pi.**
  ```
  $ sudo apt-get update
  $ sudo apt-get install -y build-essential python-dev python-pip ntpdate git
  $ sudo -H pip install --upgrade pip
  $ sudo -H pip install psutil
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

**xii) Modify settings.json**
  ```
  $ sudo nano /opt/RPi_Airbox/settings.json
  ```
  
  Check settings of *"global"*, especially *"sensor_location"*
  Check settings of each model. If you have the specific module in your RPi box, 
  please make sure the *"status"* should be *"1"* to let RPi_Airbox_loader.py to bring it up.

**xiii) Create monitor_web\sensor_values directory to store data**
  ```
  $ sudo mkdir /opt/RPi_Airbox/monitor_web/sensor_values
  ```

**xiv) Sync time with NTP server (if possible)**
  ```
  $ sudo systemctl stop ntp
  $ sudo ntpdate -s [your NTP server]
  ```

## 2. Set up DHT22 temperature and humidity sensor
Before this part, you have to connect DHT22 sensor to your RPi correctly, 
and know what GPIO Pin that you connect to DHT22 data pin.

**i) Change to /opt/RPi_Airbox/dht22 directory by input *"cd /opt/RPi_Airbox/dht22"*.**

**ii) Download DHT22 library from Github and install it.**
  ```
  $ sudo git clone https://github.com/adafruit/Adafruit_Python_DHT.git
  $ cd Adafruit_Python_DHT
  $ sudo python setup.py install
  ```
  
  After this, you can do a simple test by input *"examples/AdafruitDHT.py 2302 [GPIO Pin #]"*.
  If you can see output like *"Temp=26.3*  Humidity=44.1%"*, your DHT22 should work.

**iii) Modify settings.json. The *"gpio_pin"* should base on your wiring and make sure *"status"* of *"dht22"* is *"1"*.**

## 3. Set up MQ2 smoke sensor
Before this part, you have to connect MQ2 sensor to your RPi correctly, and know which ADC channel that you connect to MQ2 Analog pin.
(https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/)

**i) Make sure necessary python modules had been installed.**
  ```
  $ sudo -H pip install spidev
  $ sudo -H pip install apscheduler
  $ sudo -H pip install setuptools
  $ sudo -H pip install tzlocal
  ```

**ii) Check the "mq_channel" settings of "mq2" in settings.json and make sure "status" of "mq2" is "1".**

**iii) Input following command to check if MQ2 is working.**
  ```
  $ sudo python /opt/RPi_Airbox/mq2/mq2-to-csv-logger.py
  ```
  
	Wait 5 minutes if no error message.
  
  ```
  $ cat /opt/RPi_Airbox/monitor_web/sensor_values/CO_QRDC-ServerRo_latest_value.csv
  ```
  
  If you can see the value in second line, your MQ2 is ready to work.
	Don't forget to clear those records.
  
  ```
  $ sudo rm -rf /opt/RPi_Airbox/monitor_web/sensor_values/*.csv
  ```

## 4. Set up SH1106 OLED screen
Before this part, you have to connect SH1106 screen to your RPi correctly.
(https://luma-oled.readthedocs.io/en/latest/)
Because sh1106-upload.py will get the sensor values from the latest csv files from other sensors, it should not work before those csv files presented.

**i) Install necessary module**
  ```
  $ sudo apt-get install -y i2c-tools python-smbus libfreetype6-dev libjpeg-dev
  $ sudo pip -H install --upgrade pip
  $ sudo apt-get purge python-pip
  $ sudo pip -H install --upgrade luma.oled
  ```
  
  After installed, input follow command to detect your SH1106 address. The last number in the command is the i2c port number.
  
  ```
  $ i2cdetect -y 1
  ```

**ii) Base on the result of detection, modify SSH1106 settings in settings.json.**
  - "i2c_port" => "1"  (Unless, your RPi is very old model, and you can try "0")
  - "i2c_address" => "[SH1106 address]"
  - "device_height" => "64" (By default, but you still have to check your specs)
  - "status" => "1"

## 5. Set up snmp-passpersist
Because sh1106-upload.py will get the sensor values from the latest csv files from other sensors, it should not work before those csv files presented.

**i) Install necessary module**
  ```
  $ sudo pip -H install snmp-passpersist
  $ sudo apt-get install -y snmpd
  ```

**ii) modify /etc/snmp/snmpd.conf**
  If you have no idea how to modify it, you can refer to the snmpd.conf inside snmp-passpersist directory
  However, you have to modify following settings of it according to your network.
  ```
  rocommunity public  192.168.1.0/24 -V all
  =>
  rocommiuity [your ro community] [your NMS server] -V all
  ```

**iii) modify *"sensor-readings-list"* array of *"snmp-passpersist"* settings in settings.json according to your sensors. **

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
 
## 6. Set up automatical execution programs after reboot.

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
	cd /opt/RPi_Airbox
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
  0 * * * * /usr/bin/sudo ntpdate -s 10.243.20.11 >/dev/null 2>&1
  ```

## Done!
	
