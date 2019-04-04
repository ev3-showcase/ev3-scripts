import time
from datetime import datetime

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

client = mqtt.Client("publisher",transport='websockets')
client.on_connect = on_connect

#client.connect("<hostname>", 1883, 60)
client.connect("<hostname>", 9001, 60)

client.loop_start()
counter = 0

while True:
    time.sleep(2)
    counter += 1
    client.publish("test/cnt", "Cnt: %d" % counter)
    client.publish("test/datetime", str(datetime.now().date()))
