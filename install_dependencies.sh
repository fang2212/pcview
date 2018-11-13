#!/bin/bash

sudo apt install -y python3-pip # 如果没有安装pip3
https://github.com/nanomsg/nanomsg # install nanomsg lib if need
sudo pip3 install nanomsg
sudo pip3 install msgpack
sudo pip3 install opencv-python==3.4.3.18
sudo pip3 install pyserial==3.4
sudo pip3 install python-can==3.0.0