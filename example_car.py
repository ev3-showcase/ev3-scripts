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

from ev3dev2.port import LegoPort
from ev3dev2.sensor.lego import GyroSensor
from linux_metrics import cpu_stat, disk_stat, mem_stat

import ev3car
import ev3dev.brickpi3 as ev3
import picamera
from ev3car import Car, MQTTReceiver, StreamingHandler, StreamingServer
from rplidar import RPLidar

# from vidgear.gears import NetGear, PiGear, VideoGear

# Kill all processes previously running
# os.system("")

# Setup Logging: https://docs.python.org/3/library/logging.html#logging-levels
logLevel = 'DEBUG'  # DEBUG or WARNING
csvFormat = logging.Formatter('%(asctime)s,%(message)s', datefmt='%s')
today = datetime.today().strftime("%d_%m_%Y_%H_%M_%S")
logging.basicConfig(level=getattr(
    logging, logLevel), stream=sys.stderr)
logger = logging.getLogger(__name__)

# Setup File Logging
dataLoggerFile = logging.FileHandler(
    '/home/robot/data_' + today + '.log.csv', "w")
dataLogger = logging.getLogger("DATA_FILE")
dataLogger.setLevel("DEBUG")

lidarLoggerFile = logging.FileHandler(
    '/home/robot/lidar_' + today + '.log.csv', "w")
lidarLogger = logging.getLogger("LIDAR_FILE")
lidarLogger.setLevel("DEBUG")

# Write Header Rows
dataLoggerFile.setFormatter(logging.Formatter('%(message)s'))
dataLogger.addHandler(dataLoggerFile)
dataLogger.info("datetime, cpu_stat_processes, cpu_stat_percent, mem_stat_used, mem_stat_total, ultransonic, gyro_rate, gyro_angle, motor_steering_duty_cylce, motor_steering_position, motor_steering_state,motor_main_l_duty_cycle,motor_main_l_position,motor_main_l_state,motor_main_r_duty_cycle,motor_main_r_position,motor_main_r_state")
dataLogger.removeHandler(dataLoggerFile)

lidarLoggerFile.setFormatter(logging.Formatter('%(message)s'))
lidarLogger.addHandler(lidarLoggerFile)
lidarLogger.info("datetime, newValue, quality, angle, distance")
lidarLogger.removeHandler(lidarLoggerFile)

# Setup logging For Application
dataLoggerFile.setFormatter(csvFormat)
dataLogger.addHandler(dataLoggerFile)
lidarLoggerFile.setFormatter(csvFormat)
lidarLogger.addHandler(lidarLoggerFile)


# Set MQTT Variables

broker_address = os.getenv(
    'LEGOCAR_MQTT_BROKER_ADDRESS', 'message-broker-mqtt-websocket-legoracer.apps.p005.otc.mcs-paas.io')
port = int(os.getenv('LEGOCAR_MQTT_BROKER_PORT', 8000))
client_id = os.getenv('LEGOCAR_ID', 'car-' + uuid.uuid4().hex.upper()[0:6])


logging.debug(broker_address)
logging.debug(client_id)

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
        receiver = MQTTReceiver(client_id=client_id,
                                broker_address=broker_address, port=port)

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
                try:
                    ev3car.set_speed(throttle_value)
                    ev3car.steer(steering_value)
                except ValueError:
                    pass

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


def lidar():
    receiver = MQTTReceiver(client_id=client_id,
                            broker_address=broker_address, port=port)
    lidar = RPLidar('/dev/ttyUSB0')
    outfile = open('lidar.log', 'w')
    for measurment in lidar.iter_measurments():
        line = ','.join(str(v) for v in measurment)
        print(line)
        receiver.sendMessage(client_id + "/stats/lidar", line)
        lidarLogger.info(line)
        outfile.write(line + '\n')
    lidar.stop()
    lidar.disconnect()
    outfile.close()


def stats():
    receiver = MQTTReceiver(client_id=client_id,
                            broker_address=broker_address, port=port)

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

    # p = LegoPort(ev3.INPUT_1)
    # p.mode = "ev3-analog"
    # p.set_device = "lego-ev3-touch"
    # touchSensor = ev3.TouchSensor(ev3.INPUT_1)
    # logging.warning(touchSensor.value())

    while True:
        try:
            # Custom Sensor Data
            global car
            carStats = car.get_car_stats()
            used, total, _, _, _, _ = mem_stat.mem_stats()

            statsString = ','.join([str(cpu_stat.procs_running()), str(cpu_stat.cpu_percents(1)["idle"]), str(used), str(total), str(us_sensor.value()), str(gyro_sensor.rate), str(gyro_sensor.angle),
                                    str(carStats[0]), str(carStats[1]), str(carStats[2]), str(carStats[3]), str(carStats[4]), str(carStats[5]), str(carStats[6]), str(carStats[7]), str(carStats[8])])
            receiver.sendMessage(client_id + "/stats/log", statsString)
            dataLogger.info(statsString)
        except ValueError:
            logging.error("Invalid Stats")

        # time.sleep(0.5)

# datetime, Zeit – ist klar
# gyro_rate, - The rate at which the sensor is rotating, in degrees/second.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/sensors.html?highlight=gyro#ev3dev2.sensor.lego.GyroSensor.rate
# gyro_angle, - The number of degrees that the sensor has been rotated since it was put into this mode.
# https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/sensors.html?highlight=gyro#ev3dev2.sensor.lego.GyroSensor.angle
# cpu_stat_processes, Number of Processes Running
# cpu_stat_percent, percentage unused CPU
# mem_stat_used - Used Bytes of Memory
# mem_stat_total - Total Bytes of Memory
# ultransonic - Abstand in mm
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


def main():
    runInParallel(carcontrol, videofeed, stats, lidar)
    #runInParallel(carcontrol, stats)


if __name__ == '__main__':
    main()
