import struct


class Keyboard(object):
    KEY_RIGHT = 0x4f
    KEY_LEFT = 0x50
    KEY_DOWN = 0x51
    KEY_UP = 0x52
    KEY_RETURN = 0x28
    KEY_ESC = 0x29
    KEY_BACKSPACE = 0x2a
    KEY_VOLUME_UP = 0x80
    KEY_VOLUME_DOWN = 0x81

    KEY_MEDIA_NEXT = 0x01
    KEY_MEDIA_PREV = 0x02
    KEY_MEDIA_PLAY = 0x10
    KEY_MEDIA_MUTE = 0x20

    L_CTRL = 0x01
    L_SHIFT = 0x02
    L_ALT = 0x04
    L_META = 0x08
    R_CTRL = 0x10
    R_SHIFT = 0x20
    R_ALT = 0x40
    R_META = 0x80

    _EVENT_FORMAT = str('BBB5B')

    def __init__(self, device_node="/dev/hidg0"):
        self.device_node = device_node

    def release(self):
        self.press(0, 0, 0)

    def press(self, button=0, media_key=0, modifier=0):
        report = struct.pack(
            self._EVENT_FORMAT, modifier, media_key, button, 0, 0, 0, 0, 0)
        self.write(report)

    def write(self, report):
        with open(self.device_node, 'rb+') as fd:
            fd.write(report)
            fd.flush()