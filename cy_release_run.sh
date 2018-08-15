#!/bin/bash

./cy_release.sh
cd ~/env/dist
python3 run_pcviewer.py --video 1 --ip 192.168.1.233