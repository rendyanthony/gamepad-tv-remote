#!/usr/bin/env python3

import glob
import os
import subprocess
import sys

from string import Template


def apply_template(templ_fn, **kwargs):
    with open(templ_fn, 'r') as templ_fp:
        template = Template(templ_fp.read())
        return template.substitute(**kwargs)


def install(appdir):
    template_map = {
        "appdir": appdir,
        "user": "root"
    }

    subprocess.check_output(
        "apt-get install python3-evdev python3-pyudev hidrd",
        shell=True, stdout=sys.stdout)

    for xml_fn in glob.glob(os.path.join(appdir, "descriptors", "*.xml")):
        bin_fn = xml_fn.replace(".xml", ".bin")
        subprocess.check_output(
            f"hidrd-convert -i xml -o natv {xml_fn} {bin_fn}", shell=True, stdout=sys.stdout)

    required_modules = set(('dwc2', 'libcomposite'))
    with open('/etc/modules', 'r+') as fp:
        modules = set([line.strip() for line in fp.readlines() if not line.startswith('#')])
        for module in (required_modules - modules):
            fp.write(module+'\n')

    with open('/etc/systemd/system/gamepad.service', 'w') as fp:
        fp.write(apply_template('gamepad.service', **template_map))

    subprocess.check_output(
        "systemctl enable gamepad.service", shell=True, stdout=sys.stdout)
    

if __name__ == '__main__':
    install(
        os.path.abspath(os.path.dirname(__file__)))
