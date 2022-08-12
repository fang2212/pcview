#!/bin/bash

ps -ef | grep flow_view | grep -v grep | awk '{print $2}' | xargs kill -9 &
ps -ef | grep msg_fd | grep -v grep | awk '{print $2}' | xargs kill -9 &
