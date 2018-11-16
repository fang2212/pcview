#!/bin/bash

ps -ef | grep run_pcview | grep -v grep | awk '{print $2}' | xargs kill -9 

cd /home/minieye/env/dist/CANAlyst
python3 can_server.py
ps -ef | grep can_server | grep -v grep | awk '{print $2}' | xargs kill -9 

cd /home/minieye/env/dist

python3 run_pcview.py --func debug --raw_type color &
