#!/usr/bin/env python3
import json
import logging
import os
import signal
import sys
import time
import uuid

from ev3car import Car, MQTTReceiver

# Setup Logging: https://docs.python.org/3/library/logging.html#logging-levels
logLevel = 'DEBUG'
logging.basicConfig(level=getattr(
    logging, logLevel), stream=sys.stderr)
logger = logging.getLogger(__name__)

# Set MQTT Variables

broker_address = os.getenv(
    'MQTT_BROKER', 'message-broker-mqtt-websocket-fk-sc.aotp012.mcs-paas.io')
port = int(os.getenv('MQTT_PORT', 80))

simulation = False


def main():
    try:
        receiver = MQTTReceiver(broker_address=broker_address, port=port)
        ev3car = Car(simulation=simulation)

        logging.debug("Car Ready!")
        while True:
            throttle_value = receiver.throttle.value
            steering_value = receiver.steering.value

            time_diff_sec = time.time() - receiver.time.value
            # if time_diff_sec > 5.0:
            #     throttle_value = 0
            #     steering_value = 0

            # if not simulation:
            # ev3car.set_speed(throttle_value)
            ev3car.steer(steering_value)

            # logging.info('Time diff: {}, Throttle: {}, Steering: {}'.format(time_diff_sec, throttle_value, steering_value))
            time.sleep(0.01)

    except KeyboardInterrupt:
        logging.info('Termination signal received, closing connection')
        receiver.close()


if __name__ == '__main__':
    main()
