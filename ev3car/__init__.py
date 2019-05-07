#!/usr/bin/env python
import uuid
import json
import time
import logging
import sys

import paho.mqtt.client as mqtt

class Car(object):
    def __init__(self, car_name='', speed=0, steering=0, min_speed=-90, max_speed=90,min_steer=-90, max_steer=90, broker='localhost', port=1883, loglevel='WARNING'):
        self.name = self.generate_name(car_name)
        self.speed = speed
        self.steering = steering
        #self.topics = [('test/host',0),('{}/speed'.format(self.name),0),('{}/steering'.format(self.name),0)]
        self.MIN_SPEED = min_speed
        self.MAX_SPEED = max_speed
        self.MIN_STEER = min_steer
        self.MAX_STEER = max_steer
        self.broker = broker
        self.port = port

        logging.basicConfig(level=getattr(logging, loglevel.upper()),stream=sys.stdout)
        logger = logging.getLogger(__name__)

        self.mqtt_client = mqtt.Client(self.name)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

        self.mqtt_client.connect(host=self.broker, port=self.port, keepalive=60) # connect to the broker

        self.mqtt_client.loop_start()
        #self.mqtt_client.subscribe(self.topics)

        logging.info("Car created as {}".format(self.name))

    def generate_name(self, car_name):
        if car_name:
            return car_name
        else:
            return 'car-' + uuid.uuid4().hex.upper()[0:6]

    def disconnect(self):
        self.mqtt_client.disconnect()

    def on_connect(self, mqtt_client, userdata, flags, rc):
        if rc==0:
            self.connected_flag=True
            logging.info("Successful connection with rc {}".format(rc))
            self.mqtt_client.subscribe(self.topics)
        else:
            logging.critical("Connection failed with rc {}".format(rc))

    def on_disconnect(self, mqtt_client, obj, rc):
        logging.info("disconnecting")
        try:
            if rc == 0:
                logging.info("disconnect request was initiated")
            else:
                if rc >= 1:
                    error_msg = self.getErrorString(rc)
                    logging.error("disconnect occurred due to {}. Will attempt to reconnect".format(error_msg))
                    mqtt_client.reconnect()
        except Exception as e:
            logging.error("Error occurred in disconnect callback with error {}", str(e), exc_info=True)

    def on_message(self, client, userdata, msg):
        logging.info("Message received")
        loging.debug("Message content: {}".format(msg.payload))
        #self.accelerate(int(msg.payload))

    def __repr__(self):
        return("Car %s" % self.name)

    def _str_(self):
        return("%s, %d" % self.name, self.speed)

    def accelerate(self, speed):
        if speed in range(self.MIN_SPEED, self.MAX_SPEED):
            logging.debug("Previous speed was {}".format(self.speed))
            self.speed = speed
            logging.info("Speed set to {}".format(self.speed))
        else:
            raise ValueError('Value is out of range MIN_SPEED, MAX_SPEED')

    def steer(self, steering):
        if steering in range(self.MIN_STEER, self.MAX_STEER):
            self.steering = steering
        else:
            raise ValueError('Value is out of range MIN_STEER, MAX_STEER')

