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
from datetime import datetime
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

# from vidgear.gears import NetGear, PiGear, VideoGear

# Kill all processes previously running
# os.system("")

# Setup Logging: https://docs.python.org/3/library/logging.html#logging-levels
logLevel = 'DEBUG'  # DEBUG or WARNING
logging.basicConfig(level=getattr(
    logging, logLevel), stream=sys.stderr)
logger = logging.getLogger(__name__)

today = datetime.today().strftime("%d_%m_%Y_%H_%M_%S")
dataLoggerFile = logging.FileHandler(
    '/home/robot/data_' + today + '.log.csv', "w")
dataLogger = logging.getLogger("FILE")

# Write Header Row
csvHeaderFormat = logging.Formatter('%(message)s')
dataLoggerFile.setFormatter(csvHeaderFormat)
dataLogger.addHandler(dataLoggerFile)
dataLogger.info("datetime, cpu_stat_processes, cpu_stat_percent, mem_stat_used, mem_stat_total, ultransonic, gyro_rate, gyro_angle, motor_steering_duty_cylce, motor_steering_position, motor_steering_state,motor_main_l_duty_cycle,motor_main_l_position,motor_main_l_state,motor_main_r_duty_cycle,motor_main_r_position,motor_main_r_state")
dataLogger.removeHandler(dataLoggerFile)

# Setup further logging
csvFormat = logging.Formatter('%(asctime)s,%(message)s', datefmt='%s')
dataLoggerFile.setFormatter(csvFormat)
dataLogger.addHandler(dataLoggerFile)
dataLogger.setLevel("DEBUG")

# Set MQTT Variables

broker_address = os.getenv(
    'MQTT_BROKER', 'message-broker-mqtt-websocket-legoracer.apps.p005.otc.mcs-paas.io')
port = int(os.getenv('MQTT_PORT', 80))

simulation = False
car = Car(throttle_factor=100, simulation=simulation)


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

        global car
        ev3car = car

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


# def videofeed():
    # options = {"hflip": True, "exposure_mode": "auto", "iso": 800,
    #            "exposure_compensation": 15, "awb_mode": "horizon", "sensor_mode": 0}
    # # open pi video stream with defined parameters
    # stream = PiGear(resolution=(640, 480), framerate=60,
    #                 logging=True).start()
    # server = NetGear()

    # while True:
    #       # read frames from stream
    #     frame = stream.read()

    #     # check for frame if Nonetype
    #     if frame is None:
    #         break

    #     server.send(frame)
    #     # camera.start_recording(ev3car.output, format='mjpeg')
    #     # try:
    #     #     address = ('', 8000)
    #     #     server = StreamingServer(address, StreamingHandler)
    #     #     server.serve_forever()
    #     # finally:
    #     #     camera.stop_recording()


def stats():
    receiver = MQTTReceiver(broker_address=broker_address, port=port)

    p = LegoPort(ev3.INPUT_2)
    p.mode = "ev3-uart"
    p.set_device = "lego-ev3-gyro"
    time.sleep(0.1)
    gyro_sensor = ev3.GyroSensor(ev3.INPUT_2)
    gyro_sensor.mode = gyro_sensor.MODE_GYRO_G_A

    p = LegoPort(ev3.INPUT_1)
    p.mode = "ev3-uart"
    p.set_device = "lego-ev3-us"
    time.sleep(0.1)
    us_sensor = ev3.UltrasonicSensor(ev3.INPUT_1)
    us_sensor.mode = us_sensor.MODE_US_DIST_CM
    # us_sensor.MODE_US_DIST_CM = 'US_DIST_CM'

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

        global car
        carStats = car.get_car_stats()

        used, total, _, _, _, _ = mem_stat.mem_stats()

        dataLogger.info('{},{},{},{},{},{},{},{},{},{},{},{}'.format(cpu_stat.procs_running(), cpu_stat.cpu_percents(1)["idle"], used, total, us_sensor.value(), gyro_sensor.rate, gyro_sensor.angle,
                                                                     carStats[0], carStats[1], carStats[2], carStats[3], carStats[4], carStats[5], carStats[6], carStats[7], carStats[8]))


# datetime, Zeit – ist klar
# gyro_rate, - The rate at which the sensor is rotating, in degrees/second.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/sensors.html?highlight=gyro#ev3dev2.sensor.lego.GyroSensor.rate
# gyro_angle, - The number of degrees that the sensor has been rotated since it was put into this mode.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/sensors.html?highlight=gyro#ev3dev2.sensor.lego.GyroSensor.angle
# cpu_stat, Processes Running
# motor_steering_duty_cylce, - Returns the current duty cycle of the motor. Units are percent. Values are -100 to 100.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/motors.html#ev3dev2.motor.Motor.duty_cycle
# motor_steering_position, - Returns the current position of the motor in pulses of the rotary encoder. When the motor rotates clockwise, the position will increase. Likewise, rotating counter-clockwise causes the position to decrease. Writing will set the position to that value.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/motors.html#ev3dev2.motor.Motor.position
# motor_steering_state, - One of the following states:
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/motors.html#ev3dev2.motor.Motor.STATE_RUNNING
# motor_main_l_duty_cycle, - same as above
# motor_main_l_position, - same as above
# motor_main_l_state, - same as above
# motor_main_r_duty_cycle, - same as above
# motor_main_r_position, - same as above
# motor_main_r_state - same as above

        time.sleep(0.2)


def main():
    # runInParallel(carcontrol, videofeed, stats)
    runInParallel(carcontrol, stats)


if __name__ == '__main__':
    main()
