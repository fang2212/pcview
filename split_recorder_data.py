#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file    :   split_recorder_data.py    
@contact :   caofulin@minieye.cc
@date    :   2020/11/17 下午2:35
"""
import argparse
import logging
import os
import time

import cv2

from pcc import PCC
from pcc_replay import LogPlayer, prep_replay
from sink.pcc_sink import bcl
from tools.video_writer import MJPEGWriter
from utils import log_list_from_path
from turbojpeg import TurboJPEG
import numpy as np

logger = logging.getLogger(__name__)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

jpeg = TurboJPEG()


class SplitRecorder:
    """
    对log文件进行提取mark、voice标记数据
    """
    def __init__(self, log_path, voice=True, mark=False, save=None):
        self.log_path = log_path                    # log.txt路径
        self.log_dir = os.path.dirname(log_path)    # log文件夹路径
        self.save_path = save                       # 保存路径
        self.st_camera_id = -1                      # 视频开始点
        self.ed_camera_id = -1                      # 视频结束点

        self.voice = voice                          # 是否提取voice数据
        self.voice_video_frame = []                 # voice视频帧数点存储
        self.time_dt = 20                           # 控制voice提取的时间范围

        self.mark = mark                            # 是否提取mark数据
        self.marking = False                        # 是否处于mark期间
        self.mark_dir = None                        # 保存mark的文件夹路径
        self.mark_video_frame = []                  # mark视频帧数点存储
        self.mark_start = 0                         # 开始的（log.txt文档位置，时间戳）
        self.mark_end = 0                           # 结束的（log.txt文档位置，时间戳）

        self.pinpoint = None                        # 定位标记数据

        self.init()

    def init(self):
        # 初始化文件保存路径
        if self.save_path and os.path.exists(self.save_path) and os.path.isdir(self.save_path):
            self.save_path = os.path.join(self.save_path, os.path.split(self.log_dir)[-1])
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
        else:
            self.save_path = self.log_dir

    def run(self):
        if self.voice:
            self.extractor_voice()
            self.extractor_voice_video(self.voice_video_frame)
        if self.mark:
            self.extractor_mark()
            self.extractor_mark_video(self.mark_video_frame)

    def extractor_voice(self):
        """
        提取voice数据
        """
        log_sort, cfg = prep_replay(self.log_path)
        self.pinpoint = None
        with open(log_sort, "r") as rf:
            lines = rf.readlines()
            for pos, line in enumerate(lines):
                if line == "":
                    continue

                if "pinpoint" in line:
                    self.pinpoint = line

                if "voice_note" in line:
                    fields = line.split()
                    ts, us = fields[:2]
                    ts = int(ts) + int(us) / 1e6

                    # 生成文件
                    file_name = time.strftime(f"%Y-%m-%d_%H-%M-%S_voice_{fields[-1]}", time.localtime(ts))
                    data_dir = os.path.join(self.save_path, file_name)
                    if not os.path.exists(data_dir):
                        os.makedirs(data_dir)
                    video_dir = os.path.join(data_dir, "video")
                    if not os.path.exists(video_dir):
                        os.makedirs(video_dir)

                    os.system(f"cp {self.log_dir}/installation.json {data_dir}")
                    os.system(f"cp {self.log_dir}/config.json {data_dir}")

                    # 定位提取log数据
                    self.extractor_voice_log(lines, pos, ts, data_dir)

                    # 调用视频渲染
                    self.voice_video_frame.append({
                        "path": os.path.join(data_dir, "video", "video.avi"),
                        "range": (self.st_camera_id, self.ed_camera_id)
                    })
                    print("voice in ", self.st_camera_id, self.ed_camera_id)
                    self.render_video(log_sort, cfg, data_dir)

    def extractor_mark(self):
        log_sort, cfg = prep_replay(self.log_path)
        with open(log_sort, "r") as rf:
            lines = rf.readlines()
            for pos, line in enumerate(lines):
                if line == '':
                    continue

                if "pinpoint" in line:
                    self.pinpoint = line

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

        # 接入pinpoint定位数据
        if self.pinpoint:
            first_line = voice_list[0].strip().split(" ")
            pinpoint_line = self.pinpoint.strip().split(" ")
            new_log_wf.write(" ".join(first_line[:2] + pinpoint_line[2:]))

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
        self.mark_dir = os.path.join(self.save_path, self.mark_dir)
        if not os.path.exists(self.mark_dir):
            os.makedirs(self.mark_dir)
        else:
            return
        video_dir = os.path.join(self.mark_dir, "video")
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        os.system("cp {} {}".format(self.log_dir + "/installation.json", self.mark_dir))
        os.system("cp {} {}".format(self.log_dir + "/config.json", self.mark_dir))

        new_log_wf = open(os.path.join(self.mark_dir, "log.txt"), "w")
        self.st_camera_id = -1
        self.ed_camera_id = -1

        # 接入pinpoint定位数据
        if self.pinpoint:
            first_line = mark_data[0].strip().split(" ")
            pinpoint_line = self.pinpoint.strip().split(" ")
            new_log_wf.write(" ".join(first_line[:2] + pinpoint_line[2:]))

        for line in mark_data:
            if line == "":
                break
            fields = line.split()
            new_log_wf.write(line)

            if "camera" == fields[2]:
                if self.st_camera_id == -1:
                    self.st_camera_id = int(fields[3])
                self.ed_camera_id = int(fields[3])

        self.mark_video_frame.append({
            "path": os.path.join(self.mark_dir, "video", "video.avi"),
            "range": (self.st_camera_id, self.ed_camera_id)
        })
        new_log_wf.flush()
        new_log_wf.close()

    def render_video(self, log_path, cfg, save_dir):
        if os.path.exists(os.path.join(save_dir, "replay-render.avi")):
            logger.warning("已存在replay-render.avi视频文件，跳过渲染流程")
            return
        replayer = LogPlayer(log_path, cfg, ratio=0.2, start_frame=self.st_camera_id,
                             end_frame=self.ed_camera_id, loop=None, nnsend=None, real_interval=None,
                             chmain=None)
        pcc = PCC(replayer, replay=True, rlog=log_path, ipm=True, save_replay_video=save_dir, uniconf=cfg)
        replayer.start()
        pcc.start()
        replayer.join()
        pcc.control(ord('q'))

    def extractor_voice_video(self, video_list):
        """
        提取voice视频,这个方法会慢一些，因为voice有可能跟上一个voice的时间范围重合，所以需要每次都遍历一次视频集合
        @param video_list: 视频节点列表
        @return:
        """
        # 初始化视频图片生成器

        for video in video_list:
            save_path = video.get("path")
            if os.path.exists(save_path):
                continue

            video_generator = jpeg_extractor(os.path.join(self.log_dir, "video"))
            start_frame, end_frame = video.get("range")
            video_pos, jpg = next(video_generator)
            video_writer = MJPEGWriter(save_path, 1280, 720, 30)
            video_writer.write_header()
            # 跳过开头
            jump_over = start_frame - video_pos
            for i in range(jump_over):
                try:
                    next(video_generator)
                except StopIteration as e:
                    logger.debug('video 已到结尾。')
                    return
            video_pos += jump_over

            # 进入视频帧数范围
            write_range = end_frame - video_pos
            for i in range(write_range):
                try:
                    _, jpg = next(video_generator)
                except StopIteration as e:
                    logger.debug('video 已到结尾。')
                    return
                video_writer.write_frame(jpg)
            video_writer.finish_video()
            video_pos += write_range

    def extractor_mark_video(self, video_list):
        """
        提取mark视频,这个方法会快一些，因为mark不会出现重合的情况，所以只需遍历一次视频集合
        @param video_list: 视频节点列表
        @return:
        """
        # 初始化视频图片生成器
        video_generator = jpeg_extractor(os.path.join(self.log_dir, "video"))
        video_pos = 0

        for video in video_list:
            save_path = video.get("path")
            if os.path.exists(save_path):
                continue

            start_frame, end_frame = video.get("range")
            fid, jpg = next(video_generator)
            if fid and video_pos == 0:
                video_pos = fid
            video_writer = MJPEGWriter(save_path, 1280, 720, 30)
            video_writer.write_header()
            # 跳过开头
            jump_over = start_frame - video_pos
            for i in range(jump_over):
                try:
                    next(video_generator)
                except StopIteration as e:
                    logger.debug('video 已到结尾。')
                    return
            video_pos += jump_over

            # 进入视频帧数范围
            write_range = end_frame - video_pos
            for i in range(write_range):
                try:
                    _, jpg = next(video_generator)
                except StopIteration as e:
                    logger.debug('video 已到结尾。')
                    return
                video_writer.write_frame(jpg)
            video_writer.finish_video()
            video_pos += write_range


class VideoRecorder(object):
    def __init__(self, path, fps=30):
        self.fps = fps
        self._path = path
        self._writer = None
        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def set_writer(self, w=1280, h=720):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._writer = cv2.VideoWriter(self._path, fourcc, self.fps, (w, h), True)

    def write(self, data):
        self._writer.write(data)

    def release(self):
        self._writer.release()


def jpeg_extractor(video_dir):
    """
    This generator extract jpg from each of the video files in the directory.
    :param video_dir:
    :return: frame_id: rolling counter of the frame from FPGA (if valid, synced with video name)
             jpg: raw jpg bytes
    """
    buf = b''
    buf_len = int(2 * 1024 * 1024)
    video_files = sorted([x for x in os.listdir(video_dir) if x.endswith('.avi')])
    for file in video_files:
        # print("file:", file)
        file_done = False
        fcnt = 0
        fid = int(file.split('.')[0].split('_')[1])
        with open(os.path.join(video_dir, file), 'rb') as vf:
            while True:
                a = buf.find(b'\xff\xd8')
                b = buf.find(b'\xff\xd9')
                while a == -1 or b == -1:
                    read = vf.read(buf_len)
                    if len(read) == 0:
                        file_done = True
                        buf = b''
                        print('video file {} comes to an end. {} frames extracted'.format(file, fcnt))
                        break
                    buf += read
                    a = buf.find(b'\xff\xd8')
                    b = buf.find(b'\xff\xd9')

                if file_done:
                    break
                jpg = buf[a:b + 2]
                buf = buf[b + 2:]
                fcnt += 1
                jfid = int.from_bytes(jpg[24:28], byteorder="little")
                if not jpg:
                    print('extracted empty frame:', fid)
                yield fid, jpg
                if fid is not None:
                    fid = None


if __name__ == '__main__':
    # 读取参数
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='+', help='包含log.txt的路径')
    parser.add_argument('--voice', '-v', action='store_true', help='渲染voice标记视频', default=False)
    parser.add_argument('--mark', '-m', action='store_true', help='渲染mark标记视频', default=False)
    parser.add_argument('--debug', '-d', action='store_true', help='debug调试模式', default=False)
    parser.add_argument('--save', '-s', help='保存统计文件夹路径（默认当前目录）')
    args = parser.parse_args()

    # 初始化日志输出等级
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # 识别log.txt
    log_list = []
    for path in args.path:
        if not os.path.exists(path):
            continue
        log_list += log_list_from_path(path)
    if not log_list:
        logger.error("未找到log.txt文件")
        exit(1)

    if not args.voice and not args.mark:
        args.voice = True

    for log in log_list:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} start:", log)
        split = SplitRecorder(log, voice=args.voice, mark=args.mark, save=args.save)
        split.run()

