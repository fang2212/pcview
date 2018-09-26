#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage Sample: self.sh enp0s31f6 192.168.0.110"
    exit 1
fi

intname=$1
target_ip=$2

sudo mv /etc/network/interfaces /etc/network/interfaces.bak    

echo "auto lo
iface lo inet loopback

auto ${intname}
iface ${intname} inet static
address ${target_ip}
netmask 255.255.255.0" > output

sudo mv output /etc/network/interfaces

sudo /etc/init.d/networking restart

sudo ifup ${intname}