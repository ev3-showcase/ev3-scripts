#Ev3 Showcase - local scripts

## Usage

1. Start the EV3 Device by opening the Roof of the Car and pressing the Center button. 
Now EV3 Should bootup.

2. After the device is up and running (indicatorlight is now static green and does not blink anymore) make shure it is connected to the wifi. If an IP Address is shown in the top-left corner the device is connected.

3. Navigate to Filebrowser > ev3-scripts > select proto-mqttmove.py and start it

After Calibration has finished, the car will show an infomessage on the screen that is successfully connected to the Message Broker.

## Troubleshooting
- In case the car does not accept new messages it might have hung up, you need to stop the program and restart it manually. To Stop the program execution simply click the Back-button on the left side under the screen.  (Not the Control-Cross-Buttons) To restart the Program follow point 3 of usage.


## Building Instructions

| Port | Motor                 |
| ---- | --------------------- |
| A    | Main motor left Side  |
| B    | Mani motor right Side |
| C    | steering              |
| ...  | Light Sensor          |

Case: https://www.dexterindustries.com/BrickPi/brickpi-tutorials-documentation/getting-started/basics/

## Raspberry with PiBrick setup 

1. Flash the SD Card ([Link](https://www.ev3dev.org/docs/getting-started/)) with the Raspberry2/3 image. 
1.1 Edit `config.txt`
   1. Uncomment `dtoverlay=brickpi3`
   2. Uncomment the part for the camera module
2. Setup Wifi ([Link](https://www.ev3dev.org/docs/tutorials/setting-up-wifi-using-the-command-line/))
   A. `Ctrl+Alt+F6` and Login
   1. `connmanctl`
   2. `enable wifi`
   3. `scan wifi`
   3. `services`
   4. `agent on`
   5. `connect <wifi_ssid>`
   6. `quit`
3. Disable the brickman service `sudo systemctl disable brickman`, because we are operating headless, with no monitor. 
4. Copy the `autoupdate/autoupdate.sh` script to your device. 
   1. `mkdir /home/robot/autorun && /home/robot/autorun && wget https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh && chmod +x autoupdate.sh`
5. Setup the service by copying `autoupdate/car.service` to `/etc/systemd/system/car.service`. 
   1. `cd /etc/systemd/system/ && sudo wget https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/car.service && sudo daemon-reload && sudo systemctl enable car.service`
6. Install pip `sudo apt-get update && sudo apt-get install python3-pip && pip3 install -U --force-reinstall pip`
7. Do one installation of python packages `python -m pip install -r requirements.txt`
8. Use the [vscode-ev3dev-browser](https://github.com/ev3dev/vscode-ev3dev-browser) for development.

## Auto Update

Service: https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6
