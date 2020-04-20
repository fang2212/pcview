#!/bin/bash

#使用socket-can时，启用can设备
sudo ifconfig can0 down
sudo ip link set can0 up type can bitrate 250000