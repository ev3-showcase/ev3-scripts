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

1. Flash the SD Card ([Link](https://www.ev3dev.org/docs/getting-started/))
2. Setup Wifi ([Link](https://www.ev3dev.org/docs/tutorials/setting-up-wifi-using-the-command-line/))
3. Use the [vscode-ev3dev-browser](https://github.com/ev3dev/vscode-ev3dev-browser) for development.
4. Disable the brickman service `sudo systemctl disable brickman`, because we are operating headless, with no monitor. 
5. Copy the autoupdate.sh script to your device.
6. Setup the service by copying `autoupdate/car.service` to `/etc/systemd/system/rot13.service`. 

## Auto Update

Service: https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6