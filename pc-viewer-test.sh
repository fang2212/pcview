#!/bin/bash

ps -ef | grep run_pcviewer | grep -v grep | awk '{print $2}' | xargs kill -9

cd /home/minieye/repo/pc-viewer
python3 run_pcviewer.py --ip "192.168.1.251" --video 0 --path "/home/minieye/pcviewer-test-data/" --source "rec_20180526_161914" --demo 0 &
# python3 run_pcviewer.py --ip "192.168.1.251" --video 0 --path "/home/minieye/pcviewer-test-data/" --demo 1 &
