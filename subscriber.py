#!/usr/bin/env python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    client.subscribe("test/#")

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client("subscriber",transport='websockets')
client.on_connect = on_connect
client.on_message = on_message

client.connect("dasd", 9001, 60)

client.loop_forever()
