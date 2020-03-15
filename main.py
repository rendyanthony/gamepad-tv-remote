#!/usr/bin/env python3

import signal
import threading
import subprocess
import sys
import time
import logging

from evdev import ecodes, categorize

from gamepad import get_gamepad_observer
from keyboard import Keyboard
from tasks import Tasks
from tv.bravia import Bravia

log = logging.getLogger("main")
log.setLevel(logging.DEBUG)


TV_URL = "http://192.168.1.2/sony"
TV_AUTH_PSK = "1234"
TV_MAX_VOLUME = 48
TIMEOUT_DURATION = 1800  # 30 minutes


class Application(object):
    def __init__(self, tv=None):
        self._tv = tv
        self._gamepad = None
        self._gamepad_connected = threading.Event()
        self._last_activity_ts = time.time()
        self._locked = False
        self._kbd = Keyboard()
        self._stop = threading.Event()

    def set_lock_status(self, status):
        self._locked = status
        if self._locked:
            self._gamepad.set_led_colors(red=32, green=0, blue=0)
        else:
            # Display orange LED if low battery
            if self._gamepad.battery_level <= 20 and self._gamepad.battery_status == "Discharging":
                self._gamepad.set_led_colors(red=32, green=32, blue=0)
            else:
                self._gamepad.set_led_colors(red=0, green=32, blue=0)

    def on_gamepad_connected(self, gamepad_obj):
        self._gamepad = gamepad_obj
        self._last_activity_ts = time.time()
        self.set_lock_status(False)  # Make sure the gampead is unlocked
        self._gamepad_connected.set()

        log.info(f"{self._gamepad} connected")

        self._tv.turn_on()

    def on_gamepad_disconnected(self, device):
        if device == self._gamepad._udev_device:
            log.info(f"{self._gamepad} disconnected")
            self._gamepad_connected.clear()
            self._gamepad = None

    def on_key_down(self, event):
        if self._gamepad.is_pressed(ecodes.BTN_TR2):
            if event.code == ecodes.BTN_DPAD_UP:
                if self._tv.get_volume_information()['volume'] < TV_MAX_VOLUME:
                    self._kbd.press(self._kbd.KEY_VOLUME_UP)
                return

            elif event.code == ecodes.BTN_DPAD_DOWN:
                self._kbd.press(self._kbd.KEY_VOLUME_DOWN)
                return

            elif event.code == ecodes.BTN_DPAD_LEFT:
                self._kbd.press(media_key=self._kbd.KEY_MEDIA_PREV)
                return

            elif event.code == ecodes.BTN_DPAD_RIGHT:
                self._kbd.press(media_key=self._kbd.KEY_MEDIA_NEXT)
                return

        elif event.code == ecodes.BTN_DPAD_UP:
            self._kbd.press(self._kbd.KEY_UP)

        elif event.code == ecodes.BTN_DPAD_DOWN:
            self._kbd.press(self._kbd.KEY_DOWN)

        elif event.code == ecodes.BTN_DPAD_LEFT:
            self._kbd.press(self._kbd.KEY_LEFT)

        elif event.code == ecodes.BTN_DPAD_RIGHT:
            self._kbd.press(self._kbd.KEY_RIGHT)

        elif event.code in (ecodes.BTN_SOUTH,):
            self._kbd.press(self._kbd.KEY_RETURN)

    def on_key_up(self, event):
        if self._gamepad.is_pressed(ecodes.BTN_TR2):
            if event.code in (ecodes.BTN_NORTH,):
                self._tv.send_ircc_command("ActionMenu")

            if event.code in (ecodes.BTN_WEST,):
                self._kbd.press(media_key=self._kbd.KEY_MEDIA_MUTE)

        elif event.code in (ecodes.BTN_START,):
            self._kbd.press(self._kbd.KEY_RETURN, modifier=self._kbd.L_META)

        elif event.code in (ecodes.BTN_EAST,):
            self._kbd.press(self._kbd.KEY_ESC)

        elif event.code in (ecodes.BTN_NORTH,):
            self._kbd.press(self._kbd.KEY_BACKSPACE)

        elif event.code in (ecodes.BTN_WEST,):
            self._kbd.press(media_key=self._kbd.KEY_MEDIA_PLAY)

    def process_event(self, event):
        if event.type != ecodes.EV_KEY:
            return

        if not self._locked:
            self._last_activity_ts = time.time()
            if event.value != 0:
                self.on_key_down(event)
            else:
                self.on_key_up(event)
                self._kbd.release()  # Send a key-up signal

    def start(self):
        get_gamepad_observer(
            self.on_gamepad_connected,
            self.on_gamepad_disconnected).start()

        self._run()

    def stop(self, signum, frame):
        self._stop.set()

    def check_gamepad_timeout(self):
        """Disconnect gamepad it has not been used for some time"""
        if self._gamepad.is_bluetooth:
            if time.time() - self._last_activity_ts >= TIMEOUT_DURATION:
                self._gamepad_connected.clear()
                self._gamepad.disconnect()

    def check_gamepad_battery(self):
        """Check gamepad battery status"""
        if self._gamepad.has_battery:
            log.info("Gamepad battery level: {g.battery_level}% ({g.battery_status})".format(g=self._gamepad))

    def check_tv_power_status(self):
        """Disconnect bluetooth gamepad if TV is not powered on"""
        if self._gamepad.is_bluetooth and self._tv.get_power_status() != "active":
            self._gamepad_connected.clear()
            self._gamepad.disconnect()

    def create_tasks(self):
        tasks = Tasks()

        tasks.add(self.check_gamepad_timeout)
        tasks.add_periodic(300, self.check_gamepad_battery)
        if self._tv:
            tasks.add_periodic(60, self.check_tv_power_status)

        return tasks

    def _run(self):
        log.debug("_run()")

        side_tasks = self.create_tasks()

        while not self._stop.is_set():
            if not self._gamepad_connected.wait(1):
                continue
            try:
                try:
                    for event in self._gamepad.read():
                        self.process_event(event)
                except OSError as err:
                    # There seems to be an error reading the gamepad
                    # assume it got disconnected
                    log.warn("Failed to read from gamepad: {}".format(err))
                    self._gamepad_connected.clear()
                    continue

                # Lock signal
                if self._gamepad.is_pressed(ecodes.BTN_SELECT, min_duration=1):
                    self.set_lock_status(not self._locked)

                # Disconnect Signal
                if self._gamepad.is_pressed(ecodes.BTN_MODE, min_duration=4):
                    log.info("Disconnect command received")
                    self._gamepad.disconnect()
                    if self._tv:
                        self._tv.turn_off()
                    continue

                side_tasks.do()

            except Exception:
                log.exception("Unexpected error")
                break  # Stop the application and let systemd handle the restart


def main():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(levelname)5s %(name)s %(message)s')
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    logging.getLogger('tv.bravia').setLevel(logging.INFO)

    app = Application(tv=Bravia(TV_URL, auth_psk=TV_AUTH_PSK))

    signal.signal(signal.SIGTERM, app.stop)
    signal.signal(signal.SIGINT, app.stop)

    app.start()
    log.info("Bye")


if __name__ == "__main__":
    main()
