ssh pi@192.168.1.9 'mkdir /tmp/pi-key-remote/'
scp -r * pi@192.168.1.9:/tmp/pi-key-remote/
ssh pi@192.168.1.9 'sudo /tmp/pi-key-remote/setup.sh'