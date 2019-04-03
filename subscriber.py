#!/usr/bin/env python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    client.subscribe("test/#")

def on_message(client, userdata, msg):
    print(msg.topic + " " + msg.payload.decode('utf-8'))

client = mqtt.Client("subscriber",transport='websockets')
client.on_connect = on_connect
client.on_message = on_message

client.connect("<hostname>", 9001, 60)

client.loop_forever()
