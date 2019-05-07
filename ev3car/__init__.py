#!/usr/bin/env python
import uuid
import json
import time
import logging
import sys
from ev3dev2.motor import LargeMotor, MediumMotor, MoveTank, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedNativeUnits

import paho.mqtt.client as mqtt

class Car(object):
    def __init__(self, car_name='', speed=0, steering=0, min_speed=-90, max_speed=90,min_steer=-90, max_steer=90, broker='localhost', port=1883, loglevel='WARNING'):
        self.name = self.generate_name(car_name)
        self.speed = speed
        self.steering = steering
        self.MIN_SPEED = min_speed
        self.MAX_SPEED = max_speed
        self.MIN_STEER = min_steer
        self.MAX_STEER = max_steer
        self.broker = broker
        self.port = port

        self.lm = LargeMotor(OUTPUT_B)
        self.dt = MoveTank(OUTPUT_B, OUTPUT_C)
        self.sm = MediumMotor(OUTPUT_D)

        logging.basicConfig(level=getattr(logging, loglevel.upper()),stream=sys.stderr)
        logger = logging.getLogger(__name__)

        self.mqtt_client = mqtt.Client(self.name)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

        self.mqtt_client.connect(host=self.broker, port=self.port, keepalive=60) # connect to the broker

        self.mqtt_client.loop_start()

        self.calibrate_steering()

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

    def calibrate_steering(self):
        steer_info = {'max_rotation': 0, 'center_position': 0}

        # get max angle left (probably correct sides)
        sm.on(10)
        while not sm.is_overloaded:
            sleep(0.01)
        sm.off()
        logging.info('First Lock Position: %d' % sm.position)
        first_pos = sm.position

        # get max angle right
        sm.on(-10)
        while not sm.is_overloaded:
            sleep(0.01)
        sm.off()
        logging.info('Second Lock Position: %d' % sm.position)
        sec_pos = sm.position
        
        # get the total steering per side, for this get dif between the two positions and halve it
        max_steer_angle = (abs(first_pos,sec_pos)/2)
        logging.debug('Degrees to center incl. flex: %d' % max_steer_angle)

        # as we are currently at the max negative steering from determining sec_pos, using max_steer_angle should center the wheels
        sm.on_for_degrees(25, max_steer_angle)
        steer_info['center_position'] = sm.position
        logging.info('Motor zeroes at position: %d' % steer_info['center_position'])

        # halve the max steering degrees to correct flexing and play in mechanics
        steer_info['max_rot'] = round(max_steer_angle * 0.5)
        logging.info('Max steering angle: %d' % steer_info['max_rot'])
    
        return steer_info 
