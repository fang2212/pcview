# !/usr/bin/python
# -*- coding:utf8 -*-

import socket
import time
import json
from threading import Thread
from queue import Queue

import numpy as np
import cv2

if __name__ == '__main__':
    image = np.zeros((720, 1280, 3), np.uint8)
    cv2.imshow('hello', image)
    cv2.waitKey(10000)