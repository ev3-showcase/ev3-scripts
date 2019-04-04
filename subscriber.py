#!/usr/bin/env python
import signal
import uuid
import os
import json
from sys import exit

from distutils.util import strtobool

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected as %s with result code %s" % (sub_name, str(rc)))
    client.subscribe("test/#")

def on_message(client, userdata, msg):
    message = json.loads(msg.payload)
    print(message['hostname'])
    #print(json msg.payload.decode('utf-8'))

def sigterm_handler(signal, frame):
    client.disconnect()
    print('System shutting down, closing connection')
    exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

broker = os.getenv('MQTT_BROKER', 'localhost')
port =  int(os.getenv('MQTT_PORT', 1883))
sub_name = os.getenv('HOSTNAME', ('publisher-' + uuid.uuid4().hex.upper()[0:6]))
websocket = strtobool(os.getenv('MQTT_SOCKET', 'False'))

if websocket:
  print('Connecting to %s:%d as %s via websocket' % (broker, port, sub_name))
  client = mqtt.Client(sub_name,transport='websockets')
else:
  print('Connecting to %s:%d as %s' % (broker, port, sub_name))
  client = mqtt.Client(sub_name)

client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port, 60)

client.loop_forever()
