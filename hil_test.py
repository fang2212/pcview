#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   hil_test.py.py    
@contact :   caofulin@minieye.cc
@date    :   2020/12/8 下午2:06
"""
import sys
import os
from s3 import S3Client, ShellExecError, RPCError
import requests
import time

def run(path: str) -> None:

    dev_id = "test-pchil-001"
    dst_dir = "/home/minieye/upgrade_temp/"
    hil_dir = "/home/minieye/pc-hil/build/"


    # 创建 c4 客户端实例
    s3client = S3Client("https://setup-ci.minieye.tech:16330", raise_error=True)
    # 调用方法
    ret_str = s3client.ping()  # 检查s3服务器是否可连接

    if ret_str != "pong":
        print("s3 server cannot connect")
        return
    else:
        print("connected s3 server")

    soft_name = os.path.basename(path)
    print("copy %s to hil" % path)
    # copy soft
    os.system("sshpass -p minieye scp %s minieye@192.168.6.85:%s" % (path, dst_dir))

    ret_str = s3client.shell_exec(dev_id, "ls %s" % dst_dir)

    if soft_name in ret_str:
        print("copy %s successfully" % soft_name)
    else:
        print("copy %s error" % soft_name)
        return

    print("unzip soft & backup")
    s3client.shell_exec(dev_id, "cd %s ; rm -r pcc_app_bk ; mv pcc_app pcc_app_bk ; tar -zxvf %s" % (dst_dir, soft_name))

    print("start cve")
    try:
        s3client.shell_exec(dev_id, "killall pcc_app -q")
        s3client.shell_exec(dev_id, "killall pcc_app -q")
    except ShellExecError as e:
        print("killall existed cve")

    try:
        s3client.shell_exec(dev_id, 'cd {}pcc_app && nohup ./pcc_app config/cfg_tmp.json -w &'.format(dst_dir), timeout=3)
    except RPCError as e:
        print("cve started")

        # 发送录制的数据
        resp = requests.post("http://192.168.6.85:1234/control/r", data="data_tobackend")
        if resp.status_code == 200:
            print("发送录制成功")
        else:
            print("录制失败")

    # 挂载can卡, 启动case
    try:
        ret_str = s3client.shell_exec(dev_id, "cd {}; nohup echo minieye | sudo -S DISPLAY=:0 ./pchil --log_path ../data/20201112130014/log_m3-2.txt --repeat 1 &".format(hil_dir), timeout=1)
    except RPCError as e:
        print("start pchil")

    runing = True
    while runing:

        try:
            ret_str = s3client.shell_exec(dev_id, "ps -ef | grep pchil | grep -v grep")
        except ShellExecError as e:
            runing = False
            # 发送录制的数据
            resp = requests.post("http://192.168.6.85:1234/control/r", data="data_tobackend")
            if resp.status_code == 200:
                print("停止录制成功")
            else:
                print("停止录制失败")
        time.sleep(0.001)




if __name__ == '__main__':
    soft_path = "/home/cao/release/PCC_APP_20201124200224.tar.gz"
    sys.argv.append(soft_path)
    soft_path = sys.argv[1]
    run(soft_path)
    # test_bokeh()