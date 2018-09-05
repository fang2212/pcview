#!/bin/bash

ps -ef | grep run_pcview | grep -v grep | awk '{print $2}' | xargs kill -9 
cd /home/minieye/env/dist
python3 run_pcview.py --func test --raw_type color --ip 127.0.0.1 &
