#!/usr/bin/env bash
#echo "scanning for devices..."
#nmap -T5 -sP 192.168.98.2-254 > /dev/null
#cat /proc/net/arp | grep 0x2 | grep 192.168.98 > ip_mac.txt

python3 pcc_app.py config/cfg_lab.json