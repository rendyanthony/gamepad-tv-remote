# Gamepad TV Remote

Turn your bluetooth gamepad as a TV remote control using a Raspberry Pi.

> **Warning**: This project requires a Raspberry Pi Zero W board. It doesn't work with a Raspberry Pi 3 or 4 boards as it requires the Raspberry Pi to use USB gadget mode.

## How Does it Work

The Raspberry Pi Zero W is plugged in to the TV's USB port and emulates a USB keyboard device. Button presses from the gamepad is translated into keyboard presses to the TV.

## Usage 
Press the PS button on your Dualshock 4 controller to connect to the Raspberry Pi. The LED on the controller will turn green once it is recognized by the application. If you are using a Bravia TV it should turn on automatically.

Long press the PS button (4 seconds) to disconnect the controller. If you are using a Bravia TV it would be turned off automatically.

### Key Mapping

The default mapping is based on the Dualshock 4 controller.

| Gamepad Key       | Maps To                  | Remarks                   
|-------------------|--------------------------|---------------------------
| D-Pad             | Arrow Keys               |                           
| Options/Start     | Alt+Enter                | Android Home button       
| Share/Select      | -                        | Long press to lock/unlock 
| X Button          | Enter                    |                           
| Circle Button     | Escape                   | Android Back button       
| Square Button     | Media Play/Pause         |                           
| Triangle Button   | Backspace                |                           
| R2+Up, R2+Down    | Volume up/down           |                           
| R2+Left, R2+Right | Prev/Next Media          |                           
| R2+Square         | Toggle Mute              |                           
| PS Button/Mode    | Turn TV on/off           | Uses Bravia REST API

## Raspberry Pi Setup

1.  Download and write Raspbian Lite into an SD card. Make sure to enable WiFi and SSH. Insert the SD card into the Raspberry Pi and power it up. The following steps/commands should be done on the Raspberry Pi.

2.  Add `dtoverlay=dwc2` into `/boot/config.txt`.

```bash 
echo "dtoverlay=dwc2" | sudo tee -a /boot/config.txt
```

3.  Add `dwc2` and `libcomposite` into `/etc/modules`.

```bash
echo "dwc2" | sudo tee -a /etc/modules
echo "libcomposite" | sudo tee -a /etc/modules
```

4.  Install packages dependencies.

```bash
sudo apt install python3-pyudev python3-evdev hidrd
```

5.  Install the code.

```bash
git clone https://github.com/rendyanthony/gamepad-tv-remote.git
sudo gamepad-tv-remote/setup.sh
```

6.  Add the following line to `/etc/rc.local` before the `exit 0` line:

```
/opt/pi-key-remote/create_keyboard.sh
```

6.  Pair your bluetooth gampepad to the Raspberry Pi (see the guide below)

7.  Shutdown your Raspberry Pi and plug it into the TV's USB port (if you haven't)

```bash
sudo shutdown now
```

## Pair the Gamepad via Bluetooth

Follow the guide below to pair your bluetooth controller with the Raspberry Pi. The following guide is based on the Dualshock 4 controller but it should not differ much for other blueooth controllers.

1.  Start the `bluetoothctl` tool on the Raspberry Pi

```bash
sudo bluetoothctl
```

2.  Run the following two commands in the bluetoothctl application

```
agent on
default-agent
```

3.  Start scanning for devices

```
scan on
```

4.  Enter bluetooth pairing mode. On the Dualshock 4, press both the share and PS button on your Dualshock 4 controller at the same time to enter pairing mode. The LED on the Dualshock 4 will start flashing.

5.  The MAC address of the controller should show up on the command line. It should look something like this. Write down the address as we will use them in the subsequent commands.

```
[NEW] Device 00:01:6C:B4:06:7E Wireless Controller
```

6.  Type `connect` follwed with the MAC address that you got from the previous step. The LED on the Dualshock 4 should turn blue.

```
connect 00:01:6C:B4:06:7E
```

7. Type `trust` followed with the MAC address to add the controller to the trusted list. This will allow the controller to automatically connect to your Raspberry Pi

```
trust 00:01:6C:B4:06:7E
```

8.  We are now done. You can quit the tool either by pressing `Ctrl+D` or typing `quit`.
