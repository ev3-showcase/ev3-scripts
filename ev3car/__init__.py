#!/usr/bin/env python3
import ctypes
import json
import logging
import signal
import sys
import time
import uuid
from multiprocessing import Process, Value

import paho.mqtt.client as mqtt
from ev3dev2.motor import (OUTPUT_B, OUTPUT_C, OUTPUT_D, LargeMotor,
                           MediumMotor, MoveTank, SpeedNativeUnits)


# A Programming interface for the car. Takes care of initialization etc.
class Car(object):
    def __init__(self, max_throttle=900, simulation=False):
        self.throttle = max_throttle
        self.simulation = simulation

        self.__steering_force = 60

        # car parameters
        # Max steering Angle is the angle from center to max left or right
        self.max_steer_angle = 0
        self.steering_center_pos = 0
        self.max_throttle = max_throttle

        # initialize the motor objects only if not running as sim, otherwise crashes occure when the motor is not found
        if not self.simulation:
            try:
                self.mainMotors = MoveTank(OUTPUT_B, OUTPUT_C)
                self.steeringMotor = LargeMotor(OUTPUT_D)
                self.calibrate_steering()
            except:
                logging.critical(
                    "Motors or Sensors are not connected. Connect them or run in simulation mode!")

        logging.info("Car initialized.")

    def calibrate_steering(self):
        # get max angle right
        self.steeringMotor.on(self.__steering_force)
        while not self.steeringMotor.is_overloaded:
            time.sleep(0.01)
        logging.info('First Lock Position: %d' % self.steeringMotor.position)
        first_pos = self.steeringMotor.position

        # get max angle left
        self.steeringMotor.on(-1 * self.__steering_force)
        # Move steering to the other side and make sure that the motor has moved and is not blocked from moving to the right
        while not (self.steeringMotor.is_overloaded and abs(first_pos - self.steeringMotor.position) > 100):
            time.sleep(0.01)
        self.steeringMotor.off()
        logging.info('Second Lock Position: %d' % self.steeringMotor.position)
        sec_pos = self.steeringMotor.position

        # get the total steering per side
        # for this get dif between the two positions and halve it
        temp_steer_angle = (abs(first_pos-sec_pos)/2)
        # TODO: Overthink the half of the half approach, maybe use 0.9?
        self.max_steer_angle = round(temp_steer_angle * 0.5)
        logging.info('Max steering angle: {}'.format(self.max_steer_angle))
        logging.debug('Degrees to center incl. flex: %d' % temp_steer_angle)

        # as we are currently at the max negative steering from determining sec_pos
        # using max_steer_angle should center the wheels
        self.steeringMotor.on_for_degrees(
            self.__steering_force, temp_steer_angle)
        self.steering_center_pos = self.steeringMotor.position
        logging.info('Motor zeroes at position {}'.format(
            self.steering_center_pos))

        # Oversteers on way back due to drag on tires. Returns to centerposition afterwards
        try:
            val = int(temp_steer_angle)
            if(val > 0):
                logging.debug(
                    'Steering Direction is Positive, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(self.__steering_force, 40)
                self.steeringMotor.on_for_degrees(self.__steering_force, -40)
            else:
                logging.debug(
                    'Steering Direction is Negative, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(self.__steering_force, -40)
                self.steeringMotor.on_for_degrees(self.__steering_force, 40)
        except ValueError:
            logging.error("Invalid Steering Angle")
        # halve the max steering degrees to correct flexing and play in mechanics

    def steer(self, rel_angle_perc):
        assert -100 <= rel_angle_perc <= 100
        if not self.simulation:
            # Get Current Position
            curr_angle = self.steeringMotor.position

            # Get Target Angle
            logging.debug('Max Steering Angle: %d' % self.max_steer_angle)
            target_angle = self.steering_center_pos + \
                round(self.max_steer_angle*(rel_angle_perc/100))

            difference = round(curr_angle - target_angle)
            # Take According action
            logging.debug("Curr: %i | Target: %i | res: %i",
                          curr_angle, target_angle, -1 * difference)
            # steer to the left

            if not difference == 0:
                self.steeringMotor.on_for_degrees(
                    self.__steering_force, -1 * difference, block=False)

            # Or steer to the right

            # logging.debug('Resulting Rotation in Degrees %d' % steer_rotation)

            # logging.debug('New Position %d' % new_angle)
            # curr_angle = self.steeringMotor.position
            # logging.debug('Current Position %d' % self.steeringMotor.position)
            # new_angle_abs = new_angle - curr_angle
            # logging.debug('Actual Steering Delta %d' % new_angle_abs)
            # #sm.on_for_degrees(50, angle, block=False)

            # #new_angle_abs = (self.max_steer_angle * rel_angle_perc/100) - self.sm.position
            # logging.info('Steering issued for {} degrees'.format(new_angle_abs))

            # as new_angle_abs is  the destination and for_degrees will turn FOR a certain amount
            # of degrees, remove the current position from the destination position and turn
            #self.sm.on_for_degrees(50, round(new_angle_abs - self.sm.position), block=False)
            # Oversteers on way back due to drag on tires. Returns to centerposition afterwards
            # try:
            #     val = int(new_angle_abs)
            #     if(val > 0):
            #         logging.debug(
            #             'Steering Direction  is Positive, correct Tire angle now.')
            #         self.steeringMotor.on_for_degrees(25, 40)
            #         self.steeringMotor.on_for_degrees(25, -40)
            #     else:
            #         logging.debug(
            #             'Steering Direction  is Negative, correct Tire angle now.')
            #         self.steeringMotor.on_for_degrees(25, -40)
            #         self.steeringMotor.on_for_degrees(25, 40)
            # except ValueError:
            #     logging.error("Invalid Steering Angle")

    def set_speed(self, dest_speed_perc):
        # acceleration is given in percentages
        dest_speed = self.max_throttle * dest_speed_perc/100
        # acceleration happens by giving the destination speed
        if not self.simulation:
            self.mainMotors.on(left_speed=SpeedNativeUnits(
                dest_speed), right_speed=SpeedNativeUnits(dest_speed))
        logging.info("Speed was set to {}".format(dest_speed))


class MQTTReceiver():
    def __init__(self, broker_address='localhost', port=1883, keepalive=60):
        # Constants
        self.__topic_speed = 'car/speed'
        self.__topic_steer = 'car/steering'

        self.time = Value(ctypes.c_float, 0)
        self.throttle = Value(ctypes.c_int, 0)
        self.steering = Value(ctypes.c_int, 0)
        self.is_run = Value(ctypes.c_bool, True)

        self._client = mqtt.Client(
            'car-' + uuid.uuid4().hex.upper()[0:6], transport='websockets')
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        # client.username_pw_set(user, password=password)

        self._client.connect(broker_address, port, keepalive)
        logging.debug("Waiting for connection...")

        self._client.loop_start()
        # while self.is_run.value:
        # time.sleep(0.01)

        # self._p = Process(target=self._process, args=())
        # self._p.start()
        return

    def close(self):
        self._client.loop_stop()
        # self.is_run.value = False
        # self._p.join()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Successful connection with rc {}".format(rc))

            # subscribe to steering and speed topics
            client.subscribe(
                [(self.__topic_speed, 0), (self.__topic_steer, 0)])

            # apply callback to issue actions when certain messages arrive
            client.message_callback_add(self.__topic_speed, self._on_speed)
            client.message_callback_add(self.__topic_steer, self._on_steer)
            logging.debug("Subscribed to topics. Ready for Messages.")
        else:
            logging.critical("Connection failed with rc {}".format(rc))

    def _on_message(self, client, userdata, message):
        logging.info("Message received")
        logging.debug("Message content: {}".format(message.payload))
        # TODO: Make one message out of two to increase performance
        # driver_msg = json.loads(msg.payload.decode('utf-8'))
        # self.time.value = driver_msg['time']
        # self.throttle.value = driver_msg['throttle']
        # self.steering.value = driver_msg['steering']

    def _on_speed(self, client, userdata, msg):
        try:
            value = int(msg.payload.decode('utf-8'))
            if value > 100:
                value = 100
            self.throttle.value = value
            self.time.value = time.time()
        except ValueError:
            logging.error("Invalid speed")

    def _on_steer(self, client, userdata, msg):
        try:
            value = int(msg.payload.decode('utf-8'))
            if value > 100:
                value = 100
            if value < -100:
                value = -100
            self.steering.value = value
            self.time.value = time.time()
        except ValueError:
            logging.error("Invalid steering input")

    def _on_disconnect(self, mqtt_client, obj, rc):
        logging.info("disconnecting")
        try:
            if rc == 0:
                logging.info("disconnect request was initiated")
            else:
                if rc >= 1:
                    logging.error(
                        "disconnect occurred. Will attempt to reconnect", exc_info=True)
                    mqtt_client.reconnect()
        except Exception:
            logging.error(
                'Error occurred in disconnect callback with error.', exc_info=True)

    def _process(self):
        self._client.loop_start()
        while self.is_run.value:
            time.sleep(0.01)
        self._client.loop_stop()
