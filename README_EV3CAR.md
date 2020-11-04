# ev3car package
> Ignore this readme if you are just setting it up, this is for development.
## Introduction
The ev3car package is a package created to make using our demo car much easier. It takes out a whole lot of complexity regarding connecting, logging and various other topics, especially when it comes to blocking or non-blocking requests.

For this we decided to make the whole process of subscribing unblocking - getting the messages will happen in background and you can fully focus on writing the logic for your car, to properly response to messages.

## Installing the ev3car package
As this code is far from the quality needed to be published as a package, installing it currently works only by cloning the repo and installing later on. For the sanity of your system I recommend using a virtual environment.

Python 3 is recommended.

If pip is not installed run `sudo apt-get -y install python3-pip`. ([Link](https://askubuntu.com/questions/778052/installing-pip3-for-python3-on-ubuntu-16-04-lts-using-a-proxy))
```
git clone https://github.com/ev3-showcase/ev3-scripts.git
cd ev3-scripts
git checkout move2package
pip3 install .
# Or sudo python3 -m pip install -r requirements.txt
```

## The car object
The car object consists of two main parts:

* the paho mqtt client object
* the motor objects (maybe remove those later and use them as examples?)

When creating a car object, it will first take care of connecting to the broker, and then adjust the steering. Once that is done, the car will subscribe to a first topic called `test/host`. Messages coming in there will not be used.

Creating a car is rather easy:
```
from ev3car import Car
lego = Car(broker='localhost', car_name='mycar', port='1883', simulation=True, loglevel='INFO')
```

All values but `simulation` and `name` are defaults. When setting `simulation` to True, the motor objects for the ev3 will not be initialized. This can be used to test a general workflow and is currently the only way to do so, as the ev3 motors have no mock interface which could be used to emulate then (e.g. when you have no ev3 connected).

### Using the mqtt_client object
The mqtt_client is part of the car object. It's methods can be accessed via `car.mqtt_client`. This can be used to subscribe to new topics or e.g. change the log settings (per default the one from `loglevel` is used).

The documentation for this can be read on [PyPi](https://pypi.org/project/paho-mqtt/) or at [eclipse.org](https://www.eclipse.org/paho/clients/python/docs/#simple).

### Using the motor objects
When `simulation` is set to `True` (which is the default) three motors are initialized:

* LargeMotor, which can be accessed via `car.lm` and is expected to be connected to `OUTPUT_B`
* MoveTank, which can be accessed via `car.dt` and is expected to be connected to `OUTPUT_B` and `OUTPUT_C`
* MediumMotor, which can be accessed via `car.sm` and is expected to be connected to `OUTPUT_D`

In general, the official [ev3dev2 motor documentation](https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/motors.html) is probably the best place to start besides the examples included in this repository.
