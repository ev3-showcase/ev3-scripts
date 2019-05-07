from ev3car import Car
import os
import signal
from sys import exit
import time

def sigterm_handler(signal, frame):
    lego.disconnect()
    logging.info('Termination signal received, closing connection')
    exit(0)

def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    broker = os.getenv('MQTT_BROKER', 'localhost')
    port =  int(os.getenv('MQTT_PORT', 1883))

    lego = Car(broker=broker, port=port, loglevel='DEBUG')
    time.sleep(5)
    lego.mqtt_client.subscribe([('test/host',0),('car/speed',0),('car/steering',0)])
    time.sleep(60) 
    lego.disconnect()
    time.sleep(5)

if __name__ == '__main__':
    main()
