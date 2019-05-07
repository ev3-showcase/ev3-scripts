#!/usr/bin/env python3
from ev3dev2.motor import MoveTank, MediumMotor, OUTPUT_B, OUTPUT_C, OUTPUT_D

dt=MoveTank(OUTPUT_B,OUTPUT_C)
steering=MediumMotor(OUTPUT_D)

dt.on_for_seconds(left_speed=90, right_speed=90, seconds=10, block=True)
steering.on_for_degrees(90, -270)
dt.on_for_seconds(left_speed=-50, right_speed=-50, seconds=4, block=True)
steering.on_for_degrees(90, 540)
dt.on_for_seconds(left_speed=50, right_speed=50, seconds=4, block=True)
steering.on_for_degrees(90, -540)
dt.on_for_seconds(left_speed=-50, right_speed=-50, seconds=4, block=True)
steering.on_for_degrees(90, 540)
dt.on_for_seconds(left_speed=50, right_speed=50, seconds=4, block=True)
