#!/usr/bin/env bash
nmap -T5 -sP 192.168.98.2-254
cat /proc/net/arp | grep 0x2 | grep 192.168.98
