#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage Sample: self.sh 192.168.0.110"
    exit 1
fi

target_ip=$1

names=(`ls /sys/class/net -al`)
intname="nothing"

for item in ${names[@]};do
    if [[ ${item} =~ "usb" ]] 
    then
        # echo ${item}
        intname=`echo ${item##*/}`
    fi
done

echo ${intname}

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

