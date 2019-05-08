#!/usr/bin/env python
import uuid
import json
import time
import logging
import sys
from ev3dev2.motor import LargeMotor, MediumMotor, MoveTank, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedNativeUnits
import signal

import paho.mqtt.client as mqtt

class Car(object):
    def __init__(self, car_name='', broker='localhost', top_speed=900, simulation=False, port=1883, loglevel='WARNING'):
        self.name = self.generate_name(car_name)
        self.speed = top_speed
        self.port = port
        self.simulation = simulation
        self.broker = broker

        # car parameters
        self.max_steer_angle = 0
        self.steering_center_pos = 0
        self.top_speed = top_speed

        logging.basicConfig(level=getattr(logging, loglevel.upper()),stream=sys.stderr)
        logger = logging.getLogger(__name__)

        self.mqtt_client = mqtt.Client(self.name)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.enable_logger(logger=logger)

        self.mqtt_client.connect(host=self.broker, port=self.port, keepalive=60) # connect to the broker

        self.mqtt_client.loop_start()

        # ensure proper error handling
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)

        # initialize the motor objects only if not running as sim, otherwise crashes occure when the motor is not found
        if not self.simulation:
            self.lm = LargeMotor(OUTPUT_B)
            self.dt = MoveTank(OUTPUT_B, OUTPUT_C)
            self.sm = MediumMotor(OUTPUT_D)
            self.calibrate_steering()

        logging.info("Car created as {}".format(self.name))

    def generate_name(self, car_name):
        if car_name:
            return car_name
        else:
            return 'car-' + uuid.uuid4().hex.upper()[0:6]

    def disconnect(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        # I'm almost sure this is a totally wrong thing to do, but... It seems to work.
        exit(0)

    def on_connect(self, mqtt_client, userdata, flags, rc):
        if rc==0:
            self.connected_flag=True
            logging.info("Successful connection with rc {}".format(rc))
            #self.mqtt_client.subscribe(self.topics)
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

    def sigterm_handler(self, signal, frame):
        self.disconnect()
        logging.info('Termination signal received, closing connection')

    def calibrate_steering(self):
        # get max angle left (probably correct sides)
        self.sm.on(10)
        while not self.sm.is_overloaded:
            sleep(0.01)
        self.sm.off()
        logging.info('First Lock Position: %d' % sm.position)
        first_pos = self.sm.position

        # get max angle right
        self.sm.on(-10)
        while not self.sm.is_overloaded:
            sleep(0.01)
        self.sm.off()
        logging.info('Second Lock Position: %d' % sm.position)
        sec_pos = self.sm.position
        
        # get the total steering per side
        # for this get dif between the two positions and halve it
        temp_steer_angle = (abs(first_pos,sec_pos)/2)
        logging.debug('Degrees to center incl. flex: %d' % temp_steer_angle)

        # as we are currently at the max negative steering from determining sec_pos 
        # using max_steer_angle should center the wheels
        sm.on_for_degrees(25, temp_steer_angle)
        self.steering_center_pos = sm.position
        logging.info('Motor zeroes at position {}'.format(self.steering_center_pos))

        # halve the max steering degrees to correct flexing and play in mechanics
        self.max_steer_angle = round(temp_steer_angle * 0.5)
        logging.info('Max steering angle: {}'.format(self.max_steer_angle))

    def steer(self, rel_angle_perc):
        # calculates destination steering angle
        # turning distance is given in percentages
        new_angle_abs = (self.max_steer_angle * rel_angle_perc/100) - self.sm.position
        logging.info('Steering issued for {} degrees'.format(new_angle_abs))

        # as new_angle_abs is  the destination and for_degrees will turn FOR a certain amount
        # of degrees, remove the current position from the destination position and turn
        self.sm.on_for_degrees(50, round(new_angle_abs - self.sm.position), block=False)

    def set_speed(self, dest_speed_perc):
        # acceleration is given in percentages
        dest_speed = self.top_speed * dest_speed_perc/100
        # acceleration happens by giving the destination speed
        self.dt.on(left_speed=SpeedNativeUnits(dest_speed), right_speed=SpeedNativeUnits(dest_speed))
        logger.info("Speed was set to {}".format(dest_speed))
