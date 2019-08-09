#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname  $0))

echo $SCRIPT_DIR
TARGET=/opt/pi-key-remote/

test -d $TARGET && rm -rf $TARGET/* || mkdir -p $TARGET

cp -R $SCRIPT_DIR/descriptors $SCRIPT_DIR/gamepad $SCRIPT_DIR/tv $SCRIPT_DIR/*.py $SCRIPT_DIR/*.sh $SCRIPT_DIR/*.md $SCRIPT_DIR/gamepad.service $TARGET

# apt-get install python3-evdev python3-pyudev

sed "s#/home/pi/#$TARGET#" $TARGET/gamepad.service > /etc/systemd/system/gamepad.service
systemctl enable gamepad.service
systemctl restart gamepad.service
