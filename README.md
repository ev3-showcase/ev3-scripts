# Ev3 Showcase - Car

## Usage

> Make sure the Wifi the robot is configured to connect to is availabe.
1. Start the robot by connecting it to a battery. For a stable performance it is recommended to use a second battery for the PI. 
2. The Robot should start automatically. After Calibration has finished you should see data on the dashboard. 

## Troubleshooting
 - Connect to new Wifi: 
   1. Connect the PI to a Keyboard and display.
   2. Follow the "Setup Wifi" Step in the PiBrick Setup Guide. 


## Building Instructions

| Port | Motor                 |
| ---- | --------------------- |
| C    | Main motor left Side  |
| B    | Mani motor right Side |
| D    | steering              |
| S2   | Gyro                  |
| S1   | Ultraschall           |
| ...  | Light Sensor          |

Case: https://www.dexterindustries.com/BrickPi/brickpi-tutorials-documentation/getting-started/basics/

## Development Environment 

You need to install [VSCode](https://code.visualstudio.com/) and [Python](https://www.python.org/). 
Install the recommended Extensions. 

## Raspberry with PiBrick setup 

Pi Credentials:
 - Username: `robot`
 - Password: `maker`

1. Flash the SD Card ([Link](https://www.ev3dev.org/docs/getting-started/)) with the Raspberry2/3 image. 
2. Edit `config.txt` ([use this one](/config.txt))
4. Setup Wifi ([Link](https://www.ev3dev.org/docs/tutorials/setting-up-wifi-using-the-command-line/))
   A. `Ctrl+Alt+F6` and Login
   1. `connmanctl`
   2. `enable wifi`
   3. `scan wifi`
   4. `services`
   5. `agent on`
   6. `connect <wifi_ssid>`
   7. `quit`
2. Connect via [vscode-ev3dev-browser](https://github.com/ev3dev/vscode-ev3dev-browser) for development.
3. Disable the brickman service `sudo systemctl disable brickman`, because we are operating headless, with no monitor. (Password: `maker`)
4. Copy the `autoupdate/autoupdate.sh` script to your device. 
   1. `mkdir /home/robot/autorun && cd /home/robot/autorun && wget https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/autoupdate.sh && chmod +x autoupdate.sh`
6. Setup the service by copying `autoupdate/car.service` to `/etc/systemd/system/car.service`. 
   1. `cd /etc/systemd/system/ && sudo wget https://raw.githubusercontent.com/ev3-showcase/ev3-scripts/master/autoupdate/car.service && sudo systemctl daemon-reload && sudo systemctl enable car.service && sudo systemctl start car.service`
7. Install pip `sudo apt-get update && sudo apt-get install python3-pip -y && pip3 install -U --force-reinstall pip`
8. Do one installation of python packages `cd ~/autorun && python3 -m pip install -r requirements.txt`
9. Restart the device. (`sudo reboot`)

### Video Setup 

install ffmpeg
sudo modprobe bcm2835-v4l2 (from https://www.pcwelt.de/ratgeber/Mit_dem_Raspberry_Pi_die_Wohnung_ueberwachen-Sicherheit-8638548.html)

https://www.digikey.com/en/maker/blogs/streaming-live-to-youtube-and-facebook-using-raspberry-pi-camera

## Verify or monitor scripts

`journalctl -u car -f`

Kill all processes: 
`pkill -f python3`

Shutdown Device: 
`sudo shutdown -t now`

Service: 
`systemctl start car`
`systemctl stop car`
`systemctl status car`

## Auto Update

Service: https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6


## To enable the remote shutdown feature: (Still in testing)

1. `sudo visudo`
2. Add these line to `/etc/sudoers` by issuing `sudo visudo`: 
   ```
   # Cmnd alias specification
   robot ALL=/sbin/shutdown
   robot ALL=NOPASSWD:/sbin/shutdown
   ```
3. 