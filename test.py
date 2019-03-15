#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os
import time
import configparser


class Test(object):
    cfg = {1:1}

    @classmethod
    def draw(cls):
        print(cls.cfg)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('cfg.ini')
    print(config)
    test = Test()
    test.draw()
    time.sleep(10)