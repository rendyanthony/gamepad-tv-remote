import logging
import pyudev

from .ds4 import Gamepad


log = logging.getLogger("gamepad")


def get_gamepad_observer(on_gamepad_connected, on_gamepad_disconnected):
    log.debug("get_gamepad_observer()")

    def callback(device):
        if not (device.device_node and "event" in device.device_node):
            return
        if not (str(device.properties.get("ID_INPUT_JOYSTICK", 0)) == "1"):
            return
        if device.action == "add":
            on_gamepad_connected(Gamepad(device))
        if device.action == "remove":
            on_gamepad_disconnected(device)

    context = pyudev.Context()

    for device in context.list_devices(subsystem="input", ID_INPUT_JOYSTICK=1):
        if device.device_node:
            on_gamepad_connected(Gamepad(device))
            break

    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('input')
    return pyudev.MonitorObserver(monitor, callback=callback)
