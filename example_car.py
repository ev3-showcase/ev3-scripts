#!/usr/bin/env python3
import io
import json
import logging
import os
import signal
import socketserver
import sys
import time
import uuid
from http import server
from multiprocessing import Process, Value
from threading import Condition

import ev3car
from ev3car import (Car, MQTTReceiver, StreamingHandler, StreamingOutput,
                    StreamingServer)

import picamera

# Setup Logging: https://docs.python.org/3/library/logging.html#logging-levels
logLevel = 'DEBUG'  # DEBUG or WARNING
logging.basicConfig(level=getattr(
    logging, logLevel), stream=sys.stderr)
logger = logging.getLogger(__name__)

# Set MQTT Variables

broker_address = os.getenv(
    'MQTT_BROKER', 'message-broker-mqtt-websocket-fk-sc.aotp012.mcs-paas.io')
port = int(os.getenv('MQTT_PORT', 80))

simulation = False


def runInParallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


def carcontrol():
    try:
        receiver = MQTTReceiver(broker_address=broker_address, port=port)
        ev3car = Car(throttle_factor=100, simulation=simulation)

        logging.debug("Car Ready!")
        while True:
            throttle_value = receiver.throttle.value
            steering_value = receiver.steering.value

            time_diff_sec = time.time() - receiver.time.value
            # if time_diff_sec > 5.0:
            #     throttle_value = 0
            #     steering_value = 0

            if not simulation:
                ev3car.set_speed(throttle_value)
                ev3car.steer(steering_value)

            # logging.info('Time diff: {}, Throttle: {}, Steering: {}'.format(time_diff_sec, throttle_value, steering_value))
            time.sleep(0.01)

    except KeyboardInterrupt:
        logging.info('Termination signal received, closing connection')
        receiver.close()


def videofeed():
    with picamera.PiCamera(resolution='1640x1232', framerate=15) as camera:
        ev3car.output = StreamingOutput()
        # Uncomment the next line to change your Pi's Camera rotation (in degrees)
        #camera.rotation = 90
        camera.start_recording(ev3car.output, format='mjpeg')
        try:
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()


def main():
    runInParallel(carcontrol, videofeed)
    # runInParallel(videofeed)


if __name__ == '__main__':
    main()
