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

    try:
        import pyudev
        import evdev
    except ImportError as e:
        print("Missing dependency", e)
        raise

    for xml_fn in glob.glob(os.path.join(appdir, "descriptors", "*.xml")):
        bin_fn = xml_fn.replace(".xml", ".bin")
        call(f"hidrd-convert -i xml -o natv {xml_fn} {bin_fn}", shell=True)

    with open('/etc/modules', 'r+') as fp:
        modules = set([line.strip() for line in fp.readlines() if not line.startswith('#')])
        for module in set(('dwc2', 'libcomposite')) - modules:
            fp.write(f"{module}\n")

    with open('/etc/systemd/system/gamepad.service', 'w') as fp:
        fp.write(apply_template('gamepad.service', **template_map))
    call("systemctl enable gamepad.service", shell=True)


if __name__ == '__main__':
    print("Starting installation, this may take a while")
    try:
        install(
            os.path.abspath(os.path.dirname(__file__)))
        print("Installation successful!")
    except:
        print("Failed!")
        
