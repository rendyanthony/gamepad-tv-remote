import logging
import os
import pyudev
import select
import subprocess
import time

from evdev import InputDevice, ecodes, categorize


log = logging.getLogger("gamepad.ds4")


class Gamepad(object):
    def __init__(self, udev_device):
        log.debug(f"Initializing device {udev_device.device_node}")
        self._udev_device = udev_device
        self._device = InputDevice(udev_device.device_node)
        self._state = {}

        self._leds = []
        self._battery = None

        hid_device = udev_device.find_parent("hid")

        self.is_bluetooth = (udev_device.properties.get("ID_BUS") == "bluetooth")
        if self.is_bluetooth:
            self.bt_mac_address = hid_device.properties.get("HID_UNIQ")
            log.info(f"Bluetooth addr: {self.bt_mac_address}")

        for child in hid_device.children:
            if child.subsystem == "power_supply":
                log.info(f"Found power supply {child.sys_name}")
                self._battery = child
            if child.subsystem == "leds":
                log.info(f"Found led {child.sys_name}")
                self._leds.append(child)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self._device)

    def set_led_colors(self, red=0, green=0, blue=0):
        log.info(f"Setting LED colors to 0x{red:02x}{green:02x}{blue:02x}")
        for led in self._leds:
            if os.path.basename(led.sys_path).endswith("red"):
                open(os.path.join(led.sys_path, "brightness"), "w").write(f"{red}\n")
            if os.path.basename(led.sys_path).endswith("green"):
                open(os.path.join(led.sys_path, "brightness"), "w").write(f"{green}\n")
            if os.path.basename(led.sys_path).endswith("blue"):
                open(os.path.join(led.sys_path, "brightness"), "w").write(f"{blue}\n")

    @property
    def has_battery(self):
        return self._battery is not None

    @property
    def battery_level(self):
        if self._battery is None:
            return -1
        else:
            return self._battery.properties.asint("POWER_SUPPLY_CAPACITY")

    @property
    def battery_status(self):
        if self._battery is None:
            return "No battery"
        else:
            return self._battery.properties.get("POWER_SUPPLY_STATUS")

    def disconnect(self):
        log.debug("disconnect()")

        if not self.is_bluetooth:
            return  # We can only disconnect bluetooth gamepad

        proc = subprocess.Popen(
            "/usr/bin/bluetoothctl", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            log.debug("Sending disconnect signal via bluetoothctl")
            proc.communicate(
                "disconnect {}\nexit\n".format(self.bt_mac_address).encode(),
                timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

        log.info("Gamepad disconnected")

    def get_active_keys(self):
        return self._device.active_keys()

    def is_pressed(self, key, min_duration=None):
        if key in self.get_active_keys():
            if min_duration:
                if key in self._state.keys():
                    now = time.time()
                    ts, event = self._state[key]
                    if (now - ts) >= min_duration:
                        del self._state[key]
                        return True
                else:
                    return False
            else:
                return True

        return False

    def read(self):
        r, _, _ = select.select([self._device], [], [], 0.5)
        if self._device not in r:
            return

        for event in self._device.read():
            if event.code in (ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y):
                event.type = ecodes.EV_KEY
                if event.code == ecodes.ABS_HAT0X:
                    event.code = (event.value < 0) and ecodes.BTN_DPAD_LEFT or ecodes.BTN_DPAD_RIGHT
                elif event.code == ecodes.ABS_HAT0Y:
                    event.code = (event.value < 0) and ecodes.BTN_DPAD_UP or ecodes.BTN_DPAD_DOWN
                event.value = abs(event.value)

            if event.type == ecodes.EV_KEY:
                if event.value == 1:
                    self._state[event.code] = event.timestamp(), event
                if event.value == 0 and event.code in self._state.keys():
                    del self._state[event.code]

            if event.type in (ecodes.EV_KEY,):
                log.debug(categorize(event))

            yield event

    def __iter__(self):
        while True:
            for event in self.read():
                if event: yield event

    @classmethod
    def get_gamepad(cls):
        context = pyudev.Context()
        for js_device in context.list_devices(subsystem="input", ID_INPUT_JOYSTICK=1):
            if js_device.device_node:
                return cls(js_device)


if __name__ == '__main__':    
    gamepad = Gamepad.get_gamepad()
    curr_btn_state = {}
    curr_abs_state = {}
    prev_btn_state = {}
    prev_abs_state = {}
    print(gamepad._device)
    for event in iter(gamepad):
        if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
            if event.type == ecodes.EV_KEY:
                code = ecodes.BTN[event.code]
                if type(code) is list:
                    code = code[-1]
                prev_btn_state[event.code] = curr_btn_state.get(event.code, 0)
                curr_btn_state[event.code] = event.value
                print(curr_btn_state)
                print(gamepad._device.active_keys())
            else:
                code = ecodes.ABS[event.code]
                if type(code) is list:
                    code = code[-1]                
                prev_abs_state[event.code] = curr_abs_state.get(event.code, None)
                curr_abs_state[event.code] = event.value
                #if prev_abs_state[code] is not None and (abs(curr_abs_state[code] - prev_abs_state[code]) > 5):
                print(curr_abs_state)
