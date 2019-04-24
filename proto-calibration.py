#!/usr/bin/env python3
import os
import sys
import time
from time import sleep
import json
from datetime import datetime
from ev3dev2.motor import MoveTank, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D

# state constants
ON = True
OFF = False

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
    limited_steerlock = steerlock * 0.6
    debug_print('Limited Steerlock: %d' % limited_steerlock)
    max_angle = round(limited_steerlock)
    debug_print('Max Angle: %d' % limited_steerlock)
    return max_angle 

def invert(value):
    return value * -1

def main():
    '''The main function of our program'''
    
    # set the console just how we want it
    reset_console()
    set_cursor(OFF)
    set_font('Lat15-Terminus24x12')

   
    debug_print('Starting Calibration...')
    max_angle = calibrate_steering()
    debug_print('Finished Calibration.')
    debug_print('Maximum Steering Angle is: %d Degrees' % max_angle)
    debug_print('Moving to Right Max Position.')
    sm.on_for_degrees(30, max_angle, block=True)
    debug_print('Moving to Center Position.')
    sm.on_for_degrees(30, invert(max_angle), block=True)
    debug_print('Moving to Left Max Position.')
    sm.on_for_degrees(30, invert(max_angle), block=True)
    debug_print('Moving to Right Max Position.')
    sm.on_for_degrees(30, 2*max_angle, block=True)
    debug_print('Moving to Left Max Position.')
    sm.on_for_degrees(30, 2*invert(max_angle), block=True)
    debug_print('Moving to Center Position.')
    sm.on_for_degrees(30, max_angle, block=True)
    debug_print('Moving to Right Max Position.')
    sm.on_for_degrees(90, max_angle, block=True)
    debug_print('Moving to Center Position.')
    sm.on_for_degrees(90, invert(max_angle), block=True)
    debug_print('Moving to Left Max Position.')
    sm.on_for_degrees(90, invert(max_angle), block=True)
    debug_print('Moving to Right Max Position.')
    sm.on_for_degrees(90, 2*max_angle, block=True)
    debug_print('Moving to Left Max Position.')
    sm.on_for_degrees(90, 2*invert(max_angle), block=True)
    debug_print('Moving to Center Position.')
    sm.on_for_degrees(90, max_angle, block=True)
    
    #dt.on_for_seconds(50,50,3,block = True)
    #dt.on_for_seconds(-45,-45,3,block = True)
    #debug_print('Starting Calibration...')
    #calibrate_steering()
    #debug_print('Finished Calibration.')
    #debug_print('Maximum Steering Angle is: %d Degrees' % steerlock)
    #dt.on_for_seconds(50,50,3,block = True)
    #dt.on_for_seconds(-45,-45,3,block = True)


if __name__ == '__main__':
    main()