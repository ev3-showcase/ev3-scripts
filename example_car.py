#!/usr/bin/env python3
import json
import logging
import os
import signal
import sys
import time
import uuid

import paho.mqtt.client as mqtt
from ev3car import Car

# Setup Logging: https://docs.python.org/3/library/logging.html#logging-levels
logLevel = 'INFO'
logging.basicConfig(level=getattr(
    logging, logLevel), stream=sys.stderr)
logger = logging.getLogger(__name__)

# Set MQTT Variables
 
broker_address = os.getenv(
    'MQTT_BROKER', 'message-broker-mqtt-websocket-fk-sc.aotp012.mcs-paas.io')
port = int(os.getenv('MQTT_PORT', 80))

tp_speed = 'car/speed'
tp_steer = 'car/steering'

# Program variables
Connected = False   
ev3car = Car(simulation=False)


 
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Successful connection with rc {}".format(rc))

        global Connected
        Connected = True
    else:
        logging.critical("Connection failed with rc {}".format(rc))
 
def on_message(client, userdata, message):
    logging.info("Message received")
    logging.debug("Message content: {}".format(message.payload))

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
                'Error occurred in disconnect callback with error %s', str(e), exc_info=True)

def on_speed(client, userdata, msg):
    try:
        ev3car.set_speed(int(msg.payload.decode('utf-8')))
    except ValueError:
        logging.error("Invalid speed")
    except: 
        logging.error("Other Error", exc_info=True)
    # here you could now access the cars properties and change e.g. the speed or turn on various sensors`
    # decode to utf8 to avoid getting binary strings


def on_steer(client, userdata, msg):
    # that's up to you now
    try:
        ev3car.steer(int(msg.payload.decode('utf-8')))
    except ValueError:
        logger.error("Invalid steering input")
    except: 
        logging.error("Other Error", exc_info=True)

def main():
    
    client = mqtt.Client('car-' + uuid.uuid4().hex.upper()[0:6], transport='websockets')               
    # client.username_pw_set(user, password=password)    
    client.on_connect= on_connect                      
    client.on_message= on_message                      
    client.on_disconnect = on_disconnect
    
    client.connect(broker_address, port=port, keepalive=60)
    client.loop_start()       
    
    while Connected != True:
        time.sleep(0.1)
        logging.debug("Waiting for connection...")

    # subscribe to steering and speed topics
    client.subscribe([(tp_speed, 0), (tp_steer, 0)])
    # apply callback to issue actions when certain messages arrive
    client.message_callback_add(tp_speed, on_speed)
    client.message_callback_add(tp_steer, on_steer)
    logging.debug("Subscribed to topics. Ready for Messages.")

    
    try:
        while True:
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        logging.info('Termination signal received, closing connection')
        client.disconnect()
        client.loop_stop()



if __name__ == '__main__':
    main()
