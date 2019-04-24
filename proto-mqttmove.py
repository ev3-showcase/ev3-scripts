#!/usr/bin/env python3
'''Hello to the world from ev3dev.org'''
import os
import sys
import time
from time import sleep
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sound import Sound


# state constants
ON = True
OFF = False

# Load Motors

lm = LargeMotor(OUTPUT_C)
rm = LargeMotor(OUTPUT_B)
sm = MediumMotor(OUTPUT_D)
global steerlock=0


def debug_print(*args, **kwargs):
    '''Print debug messages to stderr.

    This shows up in the output panel in VS Code.
    '''
    print(*args, **kwargs, file=sys.stderr)


def reset_console():
    '''Resets the console to the default state'''
    print('\x1Bc', end='')


def set_cursor(state):
    '''Turn the cursor on or off'''
    if state:
        print('\x1B[?25h', end='')
    else:
        print('\x1B[?25l', end='')


def set_font(name):
    '''Sets the console font

    A full list of fonts can be found with `ls /usr/share/consolefonts`
    '''
    os.system('setfont ' + name)

def speedlimiter(speed):
    MAX_SPEED = 90
    MIN_SPEED = -90
    if speed > MAX_SPEED:
        speed = 90
    elif speed < MIN_SPEED:
        speed = -90
    return(speed)

def anglelimiter(speed):
    MAX_SPEED = 90
    MIN_SPEED = -90
    if speed > MAX_SPEED:
        speed = 90
    elif speed < MIN_SPEED:
        speed = -90
    return(speed)


def calibrate_steering():
    sm.on(25)
    while not sm.is_stalled:
        sleep(0.10)
    sm.off()
    debug_print('First Lock Position: %d' % sm.position)
    first_pos = sm.position
    sm.on(-25)
    while not sm.is_stalled:
        sleep(0.10)
    sm.off()
    debug_print('Second Lock Position: %d' % sm.position)
    sec_pos = sm.position
    mid_pos = (first_pos+sec_pos)/2
    debug_print('Potential Center is: %d' % mid_pos)
    sm.on_to_position(50, mid_pos)
    

def steer(angle):
    driver = Sound()
    driver.speak('I Turn my wheel %d degrees.' % angle)
    sm.on_for_degrees(50, angle)

def accel(speed = 0):
    speed = speedlimiter(speed)
    lm.on(speed)
    rm.on(speed)
    lm.on_for_seconds()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    debug_print('Connected to MQTT Broker')
    client.subscribe("test/#")
    calibrate_steering()


def on_message(client, userdata, msg):
    #debug_print('Default Encoding: %s' % sys.getdefaultencoding())
    #debug_print('StdOut Encoding: %s' % sys.stdout.encoding())
    debug_print(msg.payload.decode('utf-8'))
    message = json.loads(msg.payload.decode('utf-8'))
    print('Json Loaded')
    if message.get("steering"):
        print('Got Angle')
        debug_print('Steeringangle: %d degrees.' % message.get("steering"))
        steer(int(message.get("steering")))
        print('Steeringangle: %d degrees.' % message.get("steering"))
        debug_print('Steeringangle: %d degrees.' % message.get("steering"))
    if message.get("speed"):
        print('Got Speed')
        debug_print('Accelerate to: %d percent.' % message.get("speed"))
        accel(int(message.get("speed")))
        print('Accelerate to: %d percent.' % message.get("speed"))
    print('Command by: %s' % message.get("hostname"))
    debug_print('Command by: %s' % message.get("hostname"))

def main():
    '''The main function of our program'''

    # set the console just how we want it
    reset_console()
    set_cursor(OFF)
    set_font('Lat15-Terminus24x12')

    # print received messages to the screen of the device
    client = mqtt.Client("ev3dev")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("ts.rdy.one", 11883, 60)

    client.loop_forever()
    lm.off()
    # print something to the output panel in VS Code
    debug_print('Hello VS Code!')


if __name__ == '__main__':
    main()
