import time
import os
import uuid

from distutils.util import strtobool
from datetime import datetime

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

broker = os.getenv('MQTT_BROKER', 'localhost')
port =  os.getenv('MQTT_PORT', 1883)
pub_name = os.getenv('HOSTNAME', ('publisher-' + uuid.uuid4().hex.upper()[0:6]))
websocket = strtobool(os.getenv('MQTT_SOCKET', 'False'))

if websocket:
  print('Connecting to %s:%d as %s' % (broker, port, pub_name))
  client = mqtt.Client(pub_name,transport='websockets')
else:
  print('Connecting to %s:%d as %s via websocket' % (broker, port, pub_name))
  client = mqtt.Client(pub_name)

client.on_connect = on_connect

#client.connect("<hostname>", 1883, 60)
client.connect(broker, port, 60)

client.loop_start()
counter = 0

while True:
    time.sleep(2)
    counter += 1
    client.publish("test/cnt", "Cnt: %d" % counter)
    client.publish("test/datetime", str(datetime.now().date()))
