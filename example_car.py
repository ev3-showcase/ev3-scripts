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
from multiprocessing import Pool, Process, Value
from threading import Condition

import ev3car
from ev3car import (Car, MQTTReceiver, StreamingHandler, StreamingOutput,
                    StreamingServer)
from ev3dev2.port import LegoPort
from ev3dev2.sensor.lego import GyroSensor

import ev3dev.brickpi3 as ev3
import picamera
from linux_metrics import cpu_stat, disk_stat, mem_stat

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
        p.daemon = True
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
        # camera.rotation = 90
        camera.start_recording(ev3car.output, format='mjpeg')
        try:
            address = ('', 8000)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()


def stats():
    receiver = MQTTReceiver(broker_address=broker_address, port=port)

    p = LegoPort(ev3.INPUT_2)
    p.mode = "ev3-uart"
    p.set_device = "lego-ev3-gyro"
    time.sleep(0.1)
    gyro_sensor = ev3.GyroSensor(ev3.INPUT_2)
    gyro_sensor.mode = gyro_sensor.MODE_GYRO_G_A

    # p = LegoPort(ev3.INPUT_1)
    # p.mode = "ev3-analog"
    # p.set_device = "lego-ev3-touch"
    # touchSensor = ev3.TouchSensor(ev3.INPUT_1)
    # logging.warning(touchSensor.value())

    while True:
        # Pi Stats
        receiver.sendMessage("stats/cpu", cpu_stat.procs_running())
        logging.warning("stats")

        # Custom Sensor Data
        receiver.sendMessage("stats/gyro_rate", gyro_sensor.rate)
        receiver.sendMessage("stats/gyro_angle", gyro_sensor.angle)

        time.sleep(2)


def main():
    runInParallel(carcontrol, videofeed, stats)


if __name__ == '__main__':
    main()
