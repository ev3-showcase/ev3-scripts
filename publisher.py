import time
from datetime import datetime

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

client = mqtt.Client("publisher",transport='websockets')
client.on_connect = on_connect

#client.connect("dasd", 1883, 60)
client.connect("dasd", 9001, 60)

client.loop_start()

while True:
    time.sleep(2)
    client.publish("test/temperature", "test")
    client.publish("test/datetime", str(datetime.now()))
