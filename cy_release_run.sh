#!/bin/bash

./cy_release.sh
cd ~/env/dist
chmod a+x *.sh
python3 run_pcviewer.py --ip 192.168.1.233