#!/bin/bash

{ # This forces the whole script to be loaded so it can be overwritten later on

# Update the Car
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/example_car.py
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O car.py https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/example_car.py
fi

mkdir ev3car
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/ev3car/__init__.py
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O ./ev3car/__init__.py https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/ev3car/__init__.py
fi

# Autoinstall requirements
#wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/requirements.txt
#if [ $? -eq 0 ] ; then
#    # If the file exists download and overwrite
#    wget -O requirements.txt https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/requirements.txt
#fi
#
#pip3 install -r requirements.txt

# Update the autoupdate script itself
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O autoupdate.sh https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh
fi
chmod u+x autoupdate.sh

chmod +x car.py
brickrun ./car.py

}

