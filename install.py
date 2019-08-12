#!/usr/bin/env python3

import glob
import os
import shutil
import sys

from string import Template
from subprocess import call


def apply_template(templ_fn, **kwargs):
    with open(templ_fn, 'r') as templ_fp:
        template = Template(templ_fp.read())
        return template.substitute(**kwargs)


def install(appdir):
    template_map = {
        "appdir": appdir,
        "user": "root"
    }

    os.chdir(appdir)

    try:
        import pyudev
        import evdev
    except ImportError as e:
        print(f"Error: Missing dependency `{e.name}``")
        raise

    if not shutil.which("hidrd-convert"):
        print("Error: Can't find the `hidrd-convert` tool")
        raise Exception

    with open('/etc/modules', 'r+') as fp:
        modules = set([line.strip() for line in fp.readlines() if not line.startswith('#')])
        for module in set(('dwc2', 'libcomposite')) - modules:
            fp.write(f"{module}\n")

    with open('/etc/systemd/system/gamepad.service', 'w') as fp:
        fp.write(apply_template('services/gamepad.service', **template_map))
    call("systemctl enable gamepad.service", shell=True)

    with open('/etc/systemd/system/keyboard-device.service', 'w') as fp:
        fp.write(apply_template('services/keyboard-device.service', **template_map))
    call("systemctl enable keyboard-device.service", shell=True)


if __name__ == '__main__':
    if os.geteuid() != 0:
        print("Error: you need to have root privileges to install!")
        sys.exit(1)
    try:
        print("Starting installation, this may take a while")
        install(
            os.path.abspath(os.path.dirname(__file__)))
        print("Installation successful!")
    except:
        print("Failed!")
        sys.exit(2)
        
