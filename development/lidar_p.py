#!/usr/bin/env python3
'''Records measurments to a given file. Usage example:
$ ./record_measurments.py out.txt'''
import sys
import time

from pyrplidar import PyRPlidar
from rplidar import RPLidar

PORT_NAME = '/dev/ttyUSB0'


def run(path):
    lidar = RPLidar(PORT_NAME)
    outfile = open(path, 'w')
    try:
        print('Recording measurments... Press Crl+C to stop.')
        for measurment in lidar.iter_measurments():
            print(measurment)
            # line = '\t'.join(str(v) for v in measurment)
            # outfile.write(line + '\n')
    except KeyboardInterrupt:
        print('Stoping.')
    lidar.stop()
    lidar.disconnect()
    outfile.close()


if __name__ == '__main__':
    run(sys.argv[1])
