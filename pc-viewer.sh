#!/bin/bash

ps -ef | grep run_fpga | grep -v grep | awk '{print $2}' | xargs kill -9

cd /home/minieye/repo/pc-viewer
python3 run_fpga.py &
