#!/bin/bash

SCRIPT_DIR=$(readlink -f $(dirname  $0))

# Create gadget
mkdir /sys/kernel/config/usb_gadget/keyboard
cd /sys/kernel/config/usb_gadget/keyboard

# Add basic information
echo 0x0100 > bcdDevice  # Version 1.0.0
echo 0x0200 > bcdUSB  # USB 2.0
echo 0x00 > bDeviceClass
echo 0x00 > bDeviceProtocol
echo 0x00 > bDeviceSubClass
echo 0x08 > bMaxPacketSize0
echo 0x0104 > idProduct  # Multifunction Composite Gadget
echo 0x1d6b > idVendor  # Linux Foundation

# Create English locale
mkdir strings/0x409

echo "Raspberry Pi" > strings/0x409/manufacturer
echo "Virtual HID" > strings/0x409/product
echo "0123456789" > strings/0x409/serialnumber

# Create HID function

# Keyboard
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length  # 8-byte reports
hidrd-convert -i xml -o natv $SCRIPT_DIR/descriptors/keyboard.xml functions/hid.usb0/report_desc

# Mouse (8 Buttons, X, Y, Wheel -> 4 Bytes)
# mkdir -p functions/hid.usb1
# echo 2 > functions/hid.usb1/protocol
# echo 1 > functions/hid.usb1/subclass
# echo 4 > functions/hid.usb1/report_length
# hidrd-convert -i xml -o natv $SCRIPT_DIR/descriptors/mouse.xml functions/hid.usb1/report_desc

# Create configuration
mkdir configs/c.1
mkdir configs/c.1/strings/0x409

echo 0x80 > configs/c.1/bmAttributes #
echo 200 > configs/c.1/MaxPower # 200 mA
echo "Example configuration" > configs/c.1/strings/0x409/configuration

# Link HID function to configuration
ln -s functions/hid.usb0 configs/c.1
# ln -s functions/hid.usb1 configs/c.1

# Enable gadget
ls /sys/class/udc > UDC
