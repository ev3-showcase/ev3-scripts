#!/usr/bin/env python3
'''Hello to the world from ev3dev.org'''
import os
import sys
import time
from time import sleep
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from ev3dev2.motor import LargeMotor, MediumMotor, MoveTank, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedNativeUnits
from ev3dev2.sound import Sound


# state constants
ON = True
OFF = False

MAX_SPEED = 900

# Load Motors

lm = LargeMotor(OUTPUT_B)
dt = MoveTank(OUTPUT_B, OUTPUT_C)
sm = MediumMotor(OUTPUT_D)


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
    max_s = MAX_SPEED
    min_s = MAX_SPEED * -1
    if speed > max_s:
        speed = max_s
    elif speed < min_s:
        speed = min_s
    return(speed)

def anglelimiter(angle):
    max_angle = CENTER_POSITION + MAX_ROTATION
    min_angle = CENTER_POSITION - MAX_ROTATION
    if angle > max_angle:
        angle = max_angle
    elif angle < min_angle:
        angle = min_angle
    return(angle)

def distance(x,y):
    return abs(x-y)

def calibrate_steering():
    sm.on(10)
    while not sm.is_overloaded:
        sleep(0.01)
    sm.off()
    debug_print('First Lock Position: %d' % sm.position)
    first_pos = sm.position
    sm.on(-10)
    while not sm.is_overloaded:
        sleep(0.01)
    sm.off()
    debug_print('Second Lock Position: %d' % sm.position)
    sec_pos = sm.position
    pos_dist = distance(first_pos,sec_pos)
    steerlock = (pos_dist/2)
    debug_print('Degrees to center: %d' % steerlock)
    sm.on_for_degrees(25, steerlock)
    limited_steerlock = steerlock * 0.5
    debug_print('Limited Steerlock: %d' % limited_steerlock)
    max_rot = round(limited_steerlock)
    debug_print('Max Angle: %d' % limited_steerlock)
    steer_info = {
        'max_rotation': max_rot,
        'center_position': sm.position,
    }

    return steer_info 

STEER_INFO = calibrate_steering()
MAX_ROTATION = STEER_INFO['max_rotation']
CENTER_POSTION = STEER_INFO['center_position']   

def steer(angle_value):
    #driver = Sound()
    #driver.speak('I Turn my wheel %d degrees.' % angle)
    percent_angle = angle_value/100
    steer_rotation = round(MAX_ROTATION*percent_angle)
    #angle = anglelimiter(steer_rotation)
    new_angle = CENTER_POSTION + steer_rotation
    curr_angle = sm.position
    angle = new_angle - curr_angle
    sm.on_for_degrees(50, angle, block=False)

def accel(speed_value = 0):
    speed_percent = speed_value/100
    new_speed = round(speed_percent*MAX_SPEED)
    #speed = speedlimiter(speed)
    dt.on(left_speed=SpeedNativeUnits(new_speed), right_speed=SpeedNativeUnits(new_speed))

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    debug_print('Connected to MQTT Broker')
    client.subscribe("test/#")


def on_message(client, userdata, msg):
    #debug_print('Default Encoding: %s' % sys.getdefaultencoding())
    #debug_print('StdOut Encoding: %s' % sys.stdout.encoding())
    debug_print(msg.payload.decode('utf-8'))
    message = json.loads(msg.payload.decode('utf-8'))
    print('Json Loaded')
    #if message.get("steering"):
    steer(int(message.get("steering")))
    print('Steeringangle: %d percent.' % message.get("steering"))
    debug_print('Steeringangle: %d percent.' % message.get("steering"))
    #if message.get("speed"):
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
