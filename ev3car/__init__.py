#!/usr/bin/env python3
import json
import logging
import signal
import sys
import time
import uuid

import paho.mqtt.client as mqtt
from ev3dev2.motor import (OUTPUT_B, OUTPUT_C, OUTPUT_D, LargeMotor,
                           MediumMotor, MoveTank, SpeedNativeUnits)


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

        logging.basicConfig(level=getattr(
            logging, loglevel.upper()), stream=sys.stderr)
        logger = logging.getLogger(__name__)

        self.mqtt_client = mqtt.Client(self.name, transport='websockets')
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.enable_logger(logger=logger)

        # connect to the broker
        self.mqtt_client.connect(
            host=self.broker, port=self.port, keepalive=60)

        self.mqtt_client.loop_start()

        # ensure proper error handling
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)

        # initialize the motor objects only if not running as sim, otherwise crashes occure when the motor is not found
        if not self.simulation:
            self.mainMotors = MoveTank(OUTPUT_B, OUTPUT_C)
            self.steeringMotor = LargeMotor(OUTPUT_D)
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
        if rc == 0:
            self.connected_flag = True
            logging.info("Successful connection with rc {}".format(rc))
            # self.mqtt_client.subscribe(self.topics)
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
                    logging.error(
                        "disconnect occurred due to {}. Will attempt to reconnect".format(error_msg))
                    mqtt_client.reconnect()
        except Exception as e:
            logging.error(
                "Error occurred in disconnect callback with error {}", str(e), exc_info=True)

    def on_message(self, client, userdata, msg):
        logging.info("Message received")
        logging.debug("Message content: {}".format(msg.payload))

    def __repr__(self):
        return("Car %s" % self.name)

    def _str_(self):
        return("%s, %d" % self.name, self.speed)

    def sigterm_handler(self, signal, frame):
        self.disconnect()
        logging.info('Termination signal received, closing connection')

    def calibrate_steering(self):
        # get max angle right
        self.steeringMotor.on(60)
        while not self.steeringMotor.is_overloaded:
            time.sleep(0.01)
        logging.info('First Lock Position: %d' % self.steeringMotor.position)
        first_pos = self.steeringMotor.position

        # get max angle left
        self.steeringMotor.on(-60)
        # Move steering to the other side and make sure that the motor has moved and is not blocked from moving to the right
        while not (self.steeringMotor.is_overloaded and abs(first_pos - self.steeringMotor.position) > 100):
            time.sleep(0.01)
        self.steeringMotor.off()
        logging.info('Second Lock Position: %d' % self.steeringMotor.position)
        sec_pos = self.steeringMotor.position

        # get the total steering per side
        # for this get dif between the two positions and halve it
        temp_steer_angle = (abs(first_pos-sec_pos)/2)
        logging.debug('Degrees to center incl. flex: %d' % temp_steer_angle)

        # as we are currently at the max negative steering from determining sec_pos
        # using max_steer_angle should center the wheels
        self.steeringMotor.on_for_degrees(25, temp_steer_angle)
        self.steering_center_pos = self.steeringMotor.position
        logging.info('Motor zeroes at position {}'.format(
            self.steering_center_pos))

        # Oversteers on way back due to drag on tires. Returns to centerposition afterwards
        try:
            val = int(temp_steer_angle)
            if(val > 0):
                logging.debug(
                    'Steering Direction is Positive, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(25, 40)
                self.steeringMotor.on_for_degrees(25, -40)
            else:
                logging.debug(
                    'Steering Direction is Negative, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(25, -40)
                self.steeringMotor.on_for_degrees(25, 40)
        except ValueError:
            logger.error("Invalid Steering Angle")
        # halve the max steering degrees to correct flexing and play in mechanics
        self.max_steer_angle = round(temp_steer_angle * 0.5)
        logging.info('Max steering angle: {}'.format(self.max_steer_angle))

    def steer(self, rel_angle_perc):
        # calculates destination steering angle
        # turning distance is given in percentages
        logging.debug('Steering Input Value: %d' % rel_angle_perc)
        percent_angle = rel_angle_perc/100
        steer_rotation = round(self.max_steer_angle*percent_angle)
        logging.debug('Max Steering Angle: %d' % self.max_steer_angle)
        logging.debug('Resulting Rotation in Degrees %d' % steer_rotation)
        #angle = anglelimiter(steer_rotation)
        logging.debug('Calculated Center Position %d' %
                      self.steering_center_pos)
        new_angle = self.steering_center_pos + steer_rotation
        logging.debug('New Position %d' % new_angle)
        curr_angle = self.steeringMotor.position
        logging.debug('Current Position %d' % self.steeringMotor.position)
        new_angle_abs = new_angle - curr_angle
        logging.debug('Actual Steering Delta %d' % new_angle_abs)
        #sm.on_for_degrees(50, angle, block=False)

        #new_angle_abs = (self.max_steer_angle * rel_angle_perc/100) - self.sm.position
        logging.info('Steering issued for {} degrees'.format(new_angle_abs))

        # as new_angle_abs is  the destination and for_degrees will turn FOR a certain amount
        # of degrees, remove the current position from the destination position and turn
        if not self.simulation:
            #self.sm.on_for_degrees(50, round(new_angle_abs - self.sm.position), block=False)
            self.steeringMotor.on_for_degrees(50, new_angle_abs)
            # Oversteers on way back due to drag on tires. Returns to centerposition afterwards
            try:
                val = int(new_angle_abs)
                if(val > 0):
                    logging.debug(
                        'Steering Direction  is Positive, correct Tire angle now.')
                    self.steeringMotor.on_for_degrees(25, 40)
                    self.steeringMotor.on_for_degrees(25, -40)
                else:
                    logging.debug(
                        'Steering Direction  is Negative, correct Tire angle now.')
                    self.steeringMotor.on_for_degrees(25, -40)
                    self.steeringMotor.on_for_degrees(25, 40)
            except ValueError:
                logger.error("Invalid Steering Angle")

    def set_speed(self, dest_speed_perc):
        # acceleration is given in percentages
        dest_speed = self.top_speed * dest_speed_perc/100
        # acceleration happens by giving the destination speed
        if not self.simulation:
            self.mainMotors.on(left_speed=SpeedNativeUnits(
                dest_speed), right_speed=SpeedNativeUnits(dest_speed))
        logging.info("Speed was set to {}".format(dest_speed))
