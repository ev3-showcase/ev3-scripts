#!/usr/bin/env python
import signal
import uuid
import os
import json
from sys import exit

from distutils.util import strtobool

import paho.mqtt.client as mqtt

class Car(mqtt.Client):
    def __init__(self, car_name=('car-' + uuid.uuid4().hex.upper()[0:6]), speed=0, steering=0, min_speed=-90, max_speed=90,min_steer=-90, max_steer=90, broker='localhost', port=1883):
        self.name = car_name
        self.speed = speed
        self.steering = steering
        self.MIN_SPEED = min_speed
        self.MAX_SPEED = max_speed
        self.MIN_STEER = min_steer
        self.MAX_STEER = max_steer
        self.broker = broker
        self.port = port

        super().__init__(self.name) # actually create the client and call it like the car
        self.on_connect = on_connect

        self.connect(broker, port, 60) # connect to the broker

    def on_connect(self, userdata, flags, rc):
        if rc==0:
            self.connected_flag=True
            print("connected OK Returned code=",rc)
            self.subscribe('car/speed')
        else:
            print("Bad connection Returned code= ",rc)

    def on_message(client, userdata, msg):
        print("Got a message")
        self.accelerate(int(msg.payload))

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


def sigterm_handler(signal, frame):
    client.loop_stop(Force=True)
    client.disconnect()
    print('System shutting down, closing connection')
    exit(0)

def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    
#    client.on_connect = on_connect
#    client.on_message = on_message

    broker = os.getenv('MQTT_BROKER', 'localhost')
    port =  int(os.getenv('MQTT_PORT', 1883))

    lego = Car('legocar', broker=broker, port=port)
    lego.subscribe(('car/speed',0),('car/steering',0))

if __name__ == '__main__':
    main()
