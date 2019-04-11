#!/usr/bin/env python
import signal
import uuid
import os
import json
from sys import exit

from distutils.util import strtobool

import paho.mqtt.client as mqtt

class Car:
    def __init__(self, name, mqtt_client, speed=0, steering=0, min_speed=-90, max_speed=90,min_steer=-90, max_steer=90):
        self.name = name
        self.speed = speed
        self.steering = steering
        self.MIN_SPEED = min_speed
        self.MAX_SPEED = max_speed
        self.MIN_STEER = min_steer
        self.MAX_STEER = max_steer
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    def __repr__(self):
        return("Car %s" % self.name)

    def _str_(self):
        return("%s, %d" % self.name, self.speed)

    def accelerate(self, speed):
        if speed in range(self.MIN_SPEED, self.MAX_SPEED):
            self.speed = speed
        else:
            raise ValueError('Value is out of range MIN_SPEED, MAX_SPEED')

    def steer(self, steering):
        if steering in range(self.MIN_STEER, self.MAX_STEER):
            self.steering = steering
        else:
            raise ValueError('Value is out of range MIN_STEER, MAX_STEER')

    def on_connect(client, userdata, flags, rc):
        print(topics)
        if rc==0:
            client.connected_flag=True
            print("connected OK Returned code=",rc)
            client.subscribe('car/speed')
        else:
            print("Bad connection Returned code= ",rc)

    def on_message(client, userdata, msg):
        print("Got a message")
        self.accelerate(int(msg.payload))

def sigterm_handler(signal, frame):
    client.loop_stop(Force=True)
    client.disconnect()
    print('System shutting down, closing connection')
    exit(0)

def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    
    broker = os.getenv('MQTT_BROKER', 'localhost')
    port =  int(os.getenv('MQTT_PORT', 1883))
    sub_name = os.getenv('HOSTNAME', ('car-' + uuid.uuid4().hex.upper()[0:6]))
    websocket = strtobool(os.getenv('MQTT_SOCKET', 'False'))
    
    if websocket:
        print('Connecting to %s:%d as %s via websocket' % (broker, port, sub_name))
        client = mqtt.Client(sub_name,transport='websockets')
    else:
        print('Connecting to %s:%d as %s' % (broker, port, sub_name))
        client = mqtt.Client(sub_name)
   
#    client.on_connect = on_connect
#    client.on_message = on_message

    global topics
    global lego
   
    lego = Car('legocar', client)
    
    topics = ['car/speed', 'car/steering']
    
    client.connect(broker, port, 60)
    client.loop_start()
    while(True):
        print("A Car is driving %d speed and steering %d" % (lego.speed, lego.steering), end='\r')
    client.loop_stop()

if __name__ == '__main__':
    main()
