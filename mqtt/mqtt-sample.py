import paho.mqtt.client as mqtt
import serial

#Serial ReadLine Function
port = serial.Serial("/dev/ttyUSB0", baudrate=115200,timeout=0.05)
#上面一行根据自己情况修改，串口设备，波特率，超时时间越小串口反应越快，但是要注意把数据接收完
def readlineCR(port):
    rv = ""
    while True:
        ch = port.read()
        rv += ch
        if ch=='\r' or ch=='':
          return rv

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

# Subscribing in on_connect() means that if we lose the connection and
# reconnect then subscriptions will be renewed.
    client.subscribe("babycradle")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+":"+str(msg.payload))
#这里是把收到的MQTT信息打印到终端上面
    rcv = readlineCR(port)
    port.write("\r\n"+str(msg.payload))
#串口输出接收到的数据
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