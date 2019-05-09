#!/usr/bin/env python3
from ev3car import Car
import os
import time

broker = os.getenv('MQTT_BROKER', 'localhost')
port =  int(os.getenv('MQTT_PORT', 1883))

tp_speed = 'car/speed'
tp_steer = 'car/steering'
ev3car = Car(broker=broker, port=port, simulation=False, loglevel='DEBUG')

def on_speed(client, userdata, msg):
    try: 
        ev3car.set_speed(int(msg.payload.decode('utf-8')))
    except ValueError:
       logger.error("Invalid speed")
    # here you could now access the cars properties and change e.g. the speed or turn on various sensors`
    # decode to utf8 to avoid getting binary strings

def on_steer(client, userdata, msg):
    # that's up to you now
    try: 
        ev3car.steer(int(msg.payload.decode('utf-8')))
    except ValueError:
       logger.error("Invalid steering input")

def main():
    # subscribe to the topics you want to subscribe
    ev3car.mqtt_client.subscribe([(tp_speed,0),(tp_steer,0)])
    # apply callback to issue actions when certain messages arrive
    ev3car.mqtt_client.message_callback_add(tp_speed, on_speed)
    ev3car.mqtt_client.message_callback_add(tp_steer, on_steer)

    # do nothing for 60 seconds and wait for incoming messages which are
    # processed in the background
    time.sleep(600) 
    ev3car.disconnect()

    # as disconnecting is async as well, better wait half a second until it's done
    time.sleep(0.5)


if __name__ == '__main__':
    main()
