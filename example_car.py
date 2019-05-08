from ev3car import Car
import os
import time

broker = os.getenv('MQTT_BROKER', 'localhost')
port =  int(os.getenv('MQTT_PORT', 1883))

tp_speed = 'car/speed'
tp_steer = 'car/steering'
lego = Car(broker=broker, port=port, simulation=True, loglevel='DEBUG')

def on_speed(client, userdata, msg):
    # here you could now access the cars properties and change e.g. the speed or turn on various sensors
    print("Received speed {}".format(msg.payload.decode('utf-8')))

def main():
    # subscribe to the topics you want to subscribe
    lego.mqtt_client.subscribe([(tp_speed,0),(tp_steer,0)])
    # apply callback to issue actions when certain messages arrive
    lego.mqtt_client.message_callback_add(tp_speed, on_speed)
    lego.mqtt_client.message_callback_add(tp_steer, on_speed)

    time.sleep(60) 
    lego.disconnect()
    time.sleep(5)

if __name__ == '__main__':
    main()
