#!/bin/bash

ps -ef | grep run_pcviewer | grep -v grep | awk '{print $2}' | xargs kill -9 &
