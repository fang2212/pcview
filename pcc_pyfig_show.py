#.!/usr/bin/python
# -*- coding:utf8 -*-

import pickle


fig_obj = pickle.load(open('/home/yj/Downloads/xyvx.pyfig', 'rb'))
fig_obj.show()