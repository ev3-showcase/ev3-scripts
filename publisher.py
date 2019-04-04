import time
import os
import uuid
import signal
from sys import exit

from distutils.util import strtobool

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code " + str(rc))

def sigterm_handler(signal, frame):
    client.disconnect()
    print('System shutting down, closing connection')
    exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

broker = os.getenv('MQTT_BROKER', 'localhost')
port =  int(os.getenv('MQTT_PORT', 1883))
pub_name = os.getenv('HOSTNAME', ('publisher-' + uuid.uuid4().hex.upper()[0:6]))
websocket = strtobool(os.getenv('MQTT_SOCKET', 'False'))
wait_timer = int(os.getenv('MQTT_WAITTIME', 1))

if websocket:
  print('Connecting to %s:%d as %s via websocket' % (broker, port, pub_name))
  client = mqtt.Client(pub_name,transport='websockets')
else:
  print('Connecting to %s:%d as %s' % (broker, port, pub_name))
  client = mqtt.Client(pub_name)

client.on_connect = on_connect

#client.connect("<hostname>", 1883, 60)
client.connect(broker, port, 60)

client.loop_start()
counter = 0

while True:
    time.sleep(wait_timer)
    counter += 1
    client.publish("test/cnt", "Cnt: %d" % counter)
    client.publish("test/host", pub_name)
