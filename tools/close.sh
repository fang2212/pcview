#!/bin/bash

ps -ef | grep run_pcview | grep -v grep | awk '{print $2}' | xargs kill -9
