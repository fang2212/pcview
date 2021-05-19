#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   split_recorder_data.py    
@contact :   caofulin@minieye.cc
@date    :   2020/11/17 下午2:35
"""
import argparse
import os
import time
from pcc import PCC
from pcc_replay import LogPlayer, prep_replay
from sink.pcc_sink import bcl


class SplitRecorder:
    """
    对log文件进行提取mark、voice标记数据
    """
    def __init__(self, log_path, voice=True, mark=False):
        self.log_path = log_path                    # log.txt路径
        self.log_dir = os.path.dirname(log_path)    # log文件夹路径
        self.st_camera_id = -1                      # 视频开始点
        self.ed_camera_id = -1                      # 视频结束点

        self.voice = voice                          # 是否提取voice数据
        self.time_dt = 20                           # 控制voice提取的时间范围

        self.mark = mark                            # 是否提取mark数据
        self.marking = False                        # 是否处于mark期间
        self.mark_dir = None                        # 保存mark的文件夹路径
        self.mark_start = 0                   # 开始的（log.txt文档位置，时间戳）
        self.mark_end = 0                     # 结束的（log.txt文档位置，时间戳）

    def run(self):
        if self.voice:
            self.extractor_voice()
        if self.mark:
            self.extractor_mark()

    def extractor_voice(self):
        """
        提取voice数据
        """
        log_sort, cfg = prep_replay(self.log_path)
        with open(log_sort, "r") as rf:
            lines = rf.readlines()
            for pos, line in enumerate(lines):
                if line == "":
                    continue

                if "voice_note" in line:
                    fields = line.split()
                    ts, us = fields[:2]
                    ts = int(ts) + int(us) / 1e6

                    # 生成文件
                    data_dir = time.strftime(f"%Y-%m-%d_%H-%M-%S_voice_{fields[-1]}", time.localtime(ts))
                    data_dir = os.path.join(self.log_dir, data_dir)
                    os.system(f"cp {self.log_dir}/installation.json {data_dir}")
                    os.system(f"cp {self.log_dir}/config.json {data_dir}")
                    os.system(f"cp {self.log_dir}/video {data_dir}")

                    # 定位提取log数据
                    self.extractor_voice_log(lines, pos, ts, data_dir)

                    # 调用视频渲染
                    print("voice in ", self.st_camera_id, self.ed_camera_id)
                    self.render_video(log_sort, cfg, data_dir)

    def extractor_mark(self):
        log_sort, cfg = prep_replay(self.log_path)
        with open(log_sort, "r") as rf:
            lines = rf.readlines()
            for pos, line in enumerate(lines):
                if line == '':
                    continue

                # 格式化日志数据
                cols = line.strip().split(" ")
                if "mark" in cols[2]:
                    if "start" in cols[3]:
                        self.mark_start = pos
                        self.marking = True
                    elif "end" in cols[3]:
                        self.marking = False
                        self.mark_end = pos
                        mark_data = lines[self.mark_start:self.mark_end]
                        if not mark_data:
                            continue
                        self.extractor_mark_log(mark_data)

                        # 渲染视频数据
                        print("mark in ", self.st_camera_id, self.ed_camera_id)
                        self.render_video(log_sort, cfg, self.mark_dir)
                    continue

                if self.marking:
                    self.mark_end = pos
            # 对异常中断，没有正常结束mark的处理
            if self.marking:
                print(bcl.WARN, "未正常结束mark", bcl.ENDC)
                self.marking = False
                self.extractor_mark_log(lines[self.mark_start:])

                print("mark in ", self.st_camera_id, self.ed_camera_id)
                self.render_video(log_sort, cfg, self.mark_dir)

    def extractor_voice_log(self, log_data, pos, current_ts, save_dir):
        """
        提取voice log数据
        """
        new_log_wf = open(os.path.join(save_dir, "log.txt"), "w")
        self.st_camera_id = -1
        self.ed_camera_id = -1
        last_log_pos = len(log_data) - 1

        # 获取前time_dt时间的log数据
        start_ts = current_ts
        start_pos = pos
        while current_ts - start_ts < self.time_dt:
            start_pos -= 1
            line = log_data[start_pos]
            fields = line.split()
            ts, us = fields[:2]
            start_ts = int(ts) + int(us) / 1e6
            if "camera" == fields[2]:
                self.st_camera_id = int(fields[3])
            if start_pos == 0:
                break

        # 获取后time_dt时间的log数据
        end_ts = current_ts
        end_pos = pos
        while end_ts - current_ts < self.time_dt:
            end_pos += 1
            line = log_data[end_pos]
            fields = line.split()
            ts, us = fields[:2]
            end_ts = int(ts) + int(us) / 1e6
            if "camera" == fields[2]:
                self.ed_camera_id = int(fields[3])
            if end_pos == last_log_pos:
                break

        voice_list = log_data[start_pos:end_pos]
        for line in voice_list:
            if line == "":
                continue
            new_log_wf.write(line)
        new_log_wf.flush()
        new_log_wf.close()

    def extractor_mark_log(self, mark_data):
        """
        提取mark log数据
        """
        # 生成文件
        ts, us = mark_data[0].split()[:2]
        start_ts = int(ts) + int(us) / 1e6
        ts, us = mark_data[-1].split()[:2]
        end_ts = int(ts) + int(us) / 1e6
        print("long time:", end_ts - start_ts)
        self.mark_dir = time.strftime(f"%Y-%m-%d_%H-%M-%S_mark", time.localtime(start_ts))
        self.mark_dir = os.path.join(self.log_dir, self.mark_dir)
        os.system(f"cp {self.log_dir}/video {self.mark_dir}")
        os.system("cp {} {}".format(self.log_dir + "/installation.json", self.mark_dir))
        os.system("cp {} {}".format(self.log_dir + "/config.json", self.mark_dir))

        new_log_wf = open(os.path.join(self.mark_dir, "log.txt"), "w")
        self.st_camera_id = -1
        self.ed_camera_id = -1

        for line in mark_data:
            if line == "":
                break
            fields = line.split()
            new_log_wf.write(line)

            if "camera" == fields[2]:
                if self.st_camera_id == -1:
                    self.st_camera_id = int(fields[3])
                self.ed_camera_id = int(fields[3])

        new_log_wf.flush()
        new_log_wf.close()

    def render_video(self, log_path, cfg, save_dir):
        replayer = LogPlayer(log_path, cfg, ratio=0.2, start_frame=self.st_camera_id,
                             end_frame=self.ed_camera_id, loop=None, nnsend=None, real_interval=None,
                             chmain=None)
        pcc = PCC(replayer, replay=True, rlog=log_path, ipm=True, save_replay_video=save_dir, uniconf=cfg)
        replayer.start()
        pcc.start()
        replayer.join()
        pcc.control(ord('q'))


if __name__ == '__main__':
    # 读取参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', '-l', help='log文件路径')
    parser.add_argument('--dir', '-d', help='批量文件夹路径')
    parser.add_argument('--voice', '-v', action='store_true', help='渲染voice标记视频', default=False)
    parser.add_argument('--mark', '-m', action='store_true', help='渲染mark标记视频', default=False)
    parser.add_argument('--save', '-s', help='保存统计文件夹路径（默认当前目录）', default='.')
    args = parser.parse_args()

    # 识别log.txt
    log_list = []
    if args.log:
        if os.path.exists(args.log):
            log_list.append(args.log)
        else:
            print(args.log, "文件路径不存在\n")
            exit(0)

    # 识别文件夹的log.txt
    if args.dir:
        if os.path.exists(os.path.join(args.dir, "log.txt")):
            if os.path.exists(args.dir):
                log_list.append(os.path.join(args.dir, "log.txt"))
            else:
                print(args.dir, "文件路径不存在\n")
                exit(0)
        else:
            for f in os.listdir(args.dir):
                path = os.path.join(args.dir, f, "log.txt")
                if os.path.exists(path):
                    log_list.append(path)
                else:
                    print(f"{os.path.join(args.dir, f)}文件夹下未找到log.txt")

    if not args.voice and not args.mark:
        args.voice = True

    for log in log_list:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} start:", log)
        split = SplitRecorder(log, voice=args.voice, mark=args.mark)
        split.run()

