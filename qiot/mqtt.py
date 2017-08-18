# -*- coding: utf-8 -*-
import random
import time
from lib import qiot

"""
	This sample code demo random number value send to QIoT Suite
	requirement:
	-- opkg update
	-- opkg install distribute
	-- opkg install python-openssl
	-- easy_install pip
	-- pip install paho-mqtt
	run command: python mqtt.py
"""

"""
	Setup connection options
"""
connection = None
connection = qiot.connection(qiot.protocol.MQTT)
connection_options = connection.read_resource('./res/resourceinfo.json', '/ssl/')

"""
	Send data to QIoT Suite Lite.
"""
def on_connect(event_trigger, data):
    print "client ready"

connection.on("connect",on_connect)
connection.connect(connection_options)

while True:
    msg = str(random.randint(0, 41))
    # connection.publish_by_id("Temp", msg))
    connection.publish_by_topic("qiot/things/freeman/RPiYM/Temp", msg)

    time.sleep(1)
