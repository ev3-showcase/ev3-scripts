#!/usr/bin/env python3
import ctypes
import io
import json
import logging
import signal
import socketserver
import sys
import time
import uuid
from http import server
from multiprocessing import Process, Value
from threading import Condition

import paho.mqtt.client as mqtt
from ev3dev2.motor import (OUTPUT_B, OUTPUT_C, OUTPUT_D, LargeMotor,
                           MediumMotor, MoveTank, SpeedNativeUnits)


# A Programming interface for the car. Takes care of initialization etc.
class Car(object):
    def __init__(self, throttle_factor=100, simulation=False):
        self.simulation = simulation

        self.__steering_force = 90

        # car parameters
        # Max steering Angle is the angle from center to max left or right
        self.max_steer_angle = 0
        self.steering_center_pos = 0
        # Factor by which the speed percentage is scaled 100 for max 0 for no speed.
        self.throttle_factor = throttle_factor

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
        self.steeringMotor.on(self.__steering_force, brake=False)
        while not self.steeringMotor.is_overloaded:
            time.sleep(0.01)
        logging.info('First Lock Position: %d' % self.steeringMotor.position)
        first_pos = self.steeringMotor.position

        # get max angle left
        self.steeringMotor.on(-1 * self.__steering_force, brake=False)
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
            self.__steering_force, temp_steer_angle, brake=False)

        self.steering_center_pos = self.steeringMotor.position
        logging.info('Motor zeroes at position {}'.format(
            self.steering_center_pos))

        # Oversteers on way back due to drag on tires. Returns to centerposition afterwards
        try:
            val = int(temp_steer_angle)
            if(val > 0):
                logging.debug(
                    'Steering Direction is Positive, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(
                    self.__steering_force, 40, brake=False)
                self.steeringMotor.on_for_degrees(
                    self.__steering_force, -40, brake=False)
            else:
                logging.debug(
                    'Steering Direction is Negative, correct Tire angle now.')
                self.steeringMotor.on_for_degrees(
                    self.__steering_force, -40, brake=False)
                self.steeringMotor.on_for_degrees(
                    self.__steering_force, 40, brake=False)
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

            if difference > 4 or difference < -4:
                logging.debug("Issued Command: Steer %i with force %i", -
                              1 * difference, self.__steering_force * abs(difference)/100)
                self.steeringMotor.on_to_position(
                    self.__steering_force, target_angle, block=False)

    def set_speed(self, dest_speed_perc):
        if dest_speed_perc > 100 or dest_speed_perc < -100:
            raise NameError("Value '" + str(dest_speed_perc) +
                            "' is out of bound.")

        dest_speed = self.throttle_factor / 100 * dest_speed_perc

        if not self.simulation:
            if dest_speed == 0:
                self.mainMotors.off(brake=False)
            else:
                # The inverse of the second motor is for the purpose of our custom drive (for increased durability)
                self.mainMotors.on(left_speed=dest_speed,
                                   right_speed=-dest_speed)

        # logging.info("Speed was set to %i and %i", dest_speed, - dest_speed)


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
        return

    def close(self):
        self._client.loop_stop()
        # self.is_run.value = False
        # self._p.join()

    def sendMessage(self, topic, message):
        self._client.publish(topic, message)

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
            if value < -100:
                value = -100
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


PAGE = """\
<html>
<head>
<title>Raspberry Pi - Surveillance Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Surveillance Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info("Request")
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    global output
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


def createStreamingServer(output):
    return


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
