#!/bin/bash

# Download the autoupdate script
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O autoupdate.sh https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh
fi
chmod u+x autoupdate.sh

# Download the video-stream script
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.sh
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O video-stream.sh https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.sh
fi
chmod u+x video-stream.sh


# Download the car service
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/car.service
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O car.service https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/car.service
fi
mv car.service /etc/systemd/system/car.service


# Download the video-stream service
wget --quiet --spider https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.service
if [ $? -eq 0 ] ; then
    # If the file exists download and overwrite
    wget -O video-stream.service https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/video-stream.service
fi
mv video-stream.service /etc/systemd/system/video-stream.service

systemctl daemon-reload
systemctl enable car.service
systemctl enable video-stream.service

