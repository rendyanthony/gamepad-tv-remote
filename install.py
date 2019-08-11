#!/usr/bin/env python3

import glob
import os
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
        print(f"Error: Missing dependency '{e.name}'")
        raise

    for xml_fn in glob.glob("descriptors/*.xml"):
        bin_fn = xml_fn.replace(".xml", ".bin")
        ret = call(f"hidrd-convert -i xml -o natv {xml_fn} {bin_fn}", shell=True)
        if ret != 0:
            print(f"Error: Failed to run hidrd-convert")
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
    print("Starting installation, this may take a while")
    try:
        install(
            os.path.abspath(os.path.dirname(__file__)))
        print("Installation successful!")
    except:
        print("Failed!")
        
