#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

import time
from datetime import datetime
from math import fabs
from multiprocessing import Manager
import cv2
from turbojpeg import TurboJPEG

from net.ntrip_client import GGAReporter
from player import FlowPlayer, pcc_ui
from recorder import VideoRecorder
from recorder.convert import *
from tools.geo import *
from tools.match import is_near
from tools.transform import Transform, OrientTuner
from models.vehicle import Vehicle, get_rover_target
from models.road import Road
from tools.cpu_mem_info import *
import numpy as np
import copy
import queue
import traceback

from utils import logger

cv2.setNumThreads(0)
jpeg = TurboJPEG()


def loop_traverse(items):
    while True:
        for item in items:
            yield item

web_ui = pcc_ui


class PCC(object):
    def __init__(self, hub, replay=False, rlog=None, ipm=None, ipm_bg=False, save_replay_video=None, uniconf=None, to_web=None,
                 auto_rec=False, draw_algo=False, show_video=True, eclient=False, show_back=False):
        super(PCC, self).__init__()
        self.draw_algo = draw_algo
        self.hub = hub
        self.cfg = uniconf
        self.player = web_ui.Player(uniconf) if eclient else pcc_ui.Player(uniconf)
        self.exit = False
        self.pause = False
        self.replay = replay
        self.rlog = rlog
        self.frame_idx = 0
        self.ts0 = 0
        self.show_video = show_video        # 是否输出显示界面（包括网页、本地渲染界面）
        self.to_web = False
        self.eclient = eclient

        self.player_cache = {
            # 视频缓存
            "main": {},
            "back": {},
            "videos": {},
            # 渲染数据缓存
            "misc": {}
        }
        self.init_cache("main")
        self.init_cache('back')

        self.start_ts = 0            # cve启动时间
        self.now_fid = 0
        self.ts_now = 0
        self.cipv = {}
        self.transform = Transform(uniconf)
        self.m_g2i = self.transform.calc_g2i_matrix()
        self.ipm = None
        self.ipm_back = None
        self.show_ipm = ipm     # 是否显示俯视图
        self.set_pinpoint = False
        self.target = None
        self.rtk_pair = [{}, {}]
        self.ot = OrientTuner(uniconf)
        self.show_ipm_bg = ipm_bg
        self.auto_rec = auto_rec
        self.frame_cnt = 0
        self.refresh_rate = 20
        if uniconf.runtime.get('low_profile'):
            self.refresh_rate = 5
        self.display_interval = 1.0 / self.refresh_rate
        self.cache_del_interval = max(3 * self.display_interval, 0.4)
        self.vehicles = {'ego': Vehicle('ego')}
        self.road_info = Road()
        self.calib_data = dict()
        self.frame_cost = 0
        self.frame_cost_total = 0
        self.frame_drawn_cnt = 0
        self.video_cache = {}
        self.cache = {}
        self.run_cost = 0.05
        self.stuck_cnt = 0
        self.statistics = {}
        self.enable_auto_interval_adjust = True
        self.parse_state = True
        self.record_time_not_sync = 0         # 上一次记录时间不同步的时间，防止频繁写入日志

        self.sideview_state = loop_traverse(['back', 'front'])
        self.sv_state = 'back' if show_back else 'front'
        self.dt_from_img = 0
        self.back_img = None                # 后视图像

        self.alarm_info = {}                # 提示信息
        self.filter = []
        if replay:
            self.hub.d = Manager().dict()

        self.gga = None
        if not self.replay:
            self.en_gga = self.cfg.runtime['modules']['GGA_reporter']['enable']
        else:
            self.en_gga = False
        self.flow_player = FlowPlayer()

        self.save_replay_video = save_replay_video
        self.vw = None
        if not eclient:
            if not to_web:
                self.to_web = False
                # self.o_filter_q = queue.Queue(maxsize=20)
                cv2.namedWindow('MINIEYE-CVE')
                cv2.setMouseCallback('MINIEYE-CVE', self.left_click, '1234')
                cv2.namedWindow('adj')
                cv2.createTrackbar('Yaw  ', 'adj', 500, 1000, self.ot.update_yaw)
                cv2.createTrackbar('Pitch', 'adj', 500, 1000, self.ot.update_pitch)
                cv2.createTrackbar('Roll  ', 'adj', 500, 1000, self.ot.update_roll)
                logger.warning('{} pid:{}'.format("PCC: normal".ljust(20), os.getpid()))
            else:
                import video_server

                self.to_web = True
                self.o_msg_q = video_server.msg_q
                self.o_img_q = video_server.img_q
                # self.o_filter_q = video_server.filter_q
                logger.warning('{} pid:{}'.format("PCC: web".ljust(20), os.getpid()))
        else:
            # from player import web_ui
            from player.eclient_ui import BaseDraw

            BaseDraw.init()
            logger.warning('{} pid:{}'.format("PCC: eclient".ljust(20), os.getpid()))

        self.wav_cnt = 0
        self.audio = None

        self.space_cnt = 0

        self.cache_pause_data = []
        self.cache_pause_idx = 0
        self.cache_pause_max_len = 50

        self.recv_first_img = False

    def ts_sync_local(self):
        t = time.time()
        if self.dt_from_img == 0:
            self.dt_from_img = t - self.ts_now

        return t - self.dt_from_img

    def init_cache(self, video_source):
        if self.player_cache.get(video_source) is None:
            self.player_cache[video_source] = {}
        else:
            self.player_cache[video_source].clear()

        self.player_cache[video_source]['ts'] = 0
        self.player_cache[video_source]['img'] = open('static/img/no_video.jpg', 'rb').read()
        self.player_cache[video_source]['img_raw'] = jpeg.decode(np.fromstring(self.player_cache[video_source]['img'], np.uint8))
        self.player_cache[video_source]['frame_id'] = 0
        self.player_cache[video_source]['recv_first_img'] = False

    def clean_cache(self):
        """
        清除旧数据
        :return:
        """
        try:
            ts_now = time.time()
            for source in list(self.player_cache['misc']):
                for entity in list(self.player_cache['misc'][source]):
                    ts_a = self.player_cache['misc'][source][entity].get('ts_arrival')

                    # 对超过一定时间内的数据进行删除
                    if not ts_a or ts_now - ts_a > self.cache_del_interval:
                        del self.player_cache['misc'][source][entity]
        except Exception as e:
            logger.error('error when clean cache:{}'.format(e))

    def cache_data(self, d):
        """
        缓存数据，等待视频渲染
        :param d:
        :return:
        """
        if not d:
            return
        try:
            fid, data, source = d
        except Exception as e:
            print(e, d)
            return
        if 'arc_soft' in source or 'rt3003' in source:
            return
        if source not in self.player_cache['misc']:
            self.player_cache['misc'][source] = {}
        if isinstance(data, list):
            for d in data:
                dtype = d.get('type') if 'type' in d else 'notype'
                id = str(d.get('id')) if 'id' in d else 'noid'
                entity = dtype + '.' + id

                self.player_cache['misc'][source][entity] = d
        elif isinstance(data, dict):
            if 'video' in data['type']:
                is_main = data.get('is_main')
                if not is_main:
                    if data.get("is_back"):
                        self.recv_first_img = True
                        self.player_cache['back']['source'] = source
                        self.player_cache['back']['frame_id'] = fid
                        self.player_cache['back']['img'] = data['img']
                        self.player_cache['back']['img_raw'] = None
                        self.player_cache['back']['ts'] = data['ts']
                        self.player_cache['back']['recv_first_img'] = True
                        self.player_cache['back']['install'] = data.get("install", "video")
                        self.player_cache['back']['updated'] = True
                    else:
                        if data['source'] not in self.player_cache:
                            self.player_cache['videos'][data['source']] = {}
                        self.player_cache['videos'][data['source']] = data
                        self.player_cache['videos'][data['source']]['updated'] = True
                else:
                    # todo：需进行优化，确认是否有必要分开处理这么多字段
                    self.recv_first_img = True
                    self.player_cache['main']['frame_id'] = fid
                    self.player_cache['main']['img'] = data['img']
                    self.player_cache['main']['img_raw'] = None
                    self.player_cache['main']['recv_first_img'] = True
                    self.player_cache['main']['ts'] = data['ts']
                    self.player_cache['main']['install'] = data.get("install", "video")
                    self.player_cache['main']['updated'] = True

                    if self.replay:
                        # 退回播放数据缓存
                        self.cache_pause_data.append(copy.copy(self.player_cache))
                        if len(self.cache_pause_data) > self.cache_pause_max_len:
                            self.cache_pause_data.pop(0)
                        else:
                            self.cache_pause_idx = len(self.cache_pause_data)
                    self.check_status()
                    return True
            else:
                dtype = data.get('type') if 'type' in data else 'notype'
                id = str(data.get('id')) if 'id' in data else 'noid'
                entity = data['source'] + '.' + dtype + '.' + id

                if 'x1_data' in source:
                    if entity not in self.player_cache['misc'][source]:
                        self.player_cache['misc'][source][entity] = {"data": [], "type": "pcv_data"}
                    self.player_cache['misc'][source][entity]["data"].append(data)
                else:
                    self.player_cache['misc'][source][entity] = data

    def start(self):
        self.player.start_time = datetime.now()

        last_ts = time.time()

        while not self.exit:
            # 回放检测信号进程是否结束
            if self.replay and not self.hub.is_alive():
                logger.warning('hub exit running.')
                print('average frame cost: {:.1f}ms'.format(
                    1000 * self.frame_cost_total / self.frame_drawn_cnt)) if self.frame_drawn_cnt != 0 else None
                # 清除视频窗口
                for i in range(1, 10):
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)
                # 回放视频保存对象
                if self.vw is not None:
                    self.vw.release()
                # if self.eclient:
                #     BaseDraw.close()
                return

            # 从信号进程取出数据
            begin_ts = time.time()
            d = self.hub.pop_common()
            if d:
                # 处理数据
                pop_ts = time.time()
                self.statistics['frame_popping_cost'] = '{:.2f}'.format(1000 * (pop_ts - begin_ts))
                # 缓存信号数据，等待视频渲染
                new_frame = self.cache_data(d)
                if not new_frame:
                    continue

                if new_frame:
                    self.frame_cnt += 1
                    if self.frame_cnt > 500:
                        self.player.start_time = datetime.now()
                        self.frame_cnt = 1

                cache_ts = time.time()
                self.statistics['frame_caching_cost'] = '{:.2f}'.format(1000 * (cache_ts - pop_ts))
            else:
                if self.replay:
                    time.sleep(0.01)
                    continue

            # render begins
            if self.replay or begin_ts - last_ts > self.display_interval:
                # 监听窗口按键事件
                self.handle_keyboard()
                last_ts = time.time()
                self.render(self.frame_cnt)
                after_render_ts = time.time()
                self.statistics['frame_rendering_cost'] = '{:.2f}'.format(1000 * (after_render_ts - begin_ts))
                self.run_cost = self.run_cost * 0.9 + (after_render_ts - begin_ts) * 0.1
            else:
                time.sleep(0.001)
            self.statistics['refreshing_rate'] = '{:.1f}'.format(1.0 / self.display_interval)

        self.hub.close()

    def render(self, frame_cnt, show=True):
        if show:
            if self.eclient:
                self.web_draw(self.cache, frame_cnt)
            else:
                img_rendered = self.draw(frame_cnt)  # 处理图片，渲染数据信息
                if img_rendered is None:
                    return
                # ts_render = time.time()
                if self.to_web:
                    self.statistics['frame_total_cost'] = '{:.2f}ms'.format(self.frame_cost * 1000)
                    self.o_img_q.put(img_rendered)
                else:
                    cv2.imshow('MINIEYE-CVE', img_rendered)

                if self.recv_first_img:
                    self.save_rendered(img_rendered)

        # 暂停的时候保持画面窗口
        while self.replay and self.pause:
            self.handle_keyboard()
            if not self.eclient:
                comb = self.draw(frame_cnt)
                if self.replay:
                    cv2.imshow('MINIEYE-CVE', comb)

            time.sleep(0.1)

        # 清除已渲染的数据
        self.clean_cache()

        if self.replay:
            self.hub.pause(False)
            if self.hub.d:
                frame_cnt += self.hub.d['replay_speed'] - 1

        if self.auto_rec:
            self.auto_rec = False
            self.start_rec()

    def show_alarm_info(self, img):
        now = time.time()

        for i, key in enumerate(self.alarm_info):
            if self.alarm_info[key] > now:
                cv2.putText(img, key, (10, i*60 + 300), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 0, 255), 2)

    def resize_img(self, img):
        """
        统一图像大小
        :param img:
        :return:
        """
        if img.shape[1] > 1280:
            fx = 1280 / img.shape[1]
            img = cv2.resize(img, None, fx=fx, fy=fx)
        if img.shape[0] > 960:
            fx = 960 / img.shape[0]
            img = cv2.resize(img, None, fx=fx, fy=fx)
        return img

    def web_draw(self, mess, frame_cnt):
        t0 = time.time()
        self.player.draw_img(mess["img"])

        if self.show_ipm:
            self.m_g2i = self.transform.calc_g2i_matrix()

            self.ipm = np.zeros([720, 480, 3], np.uint8)
            self.ipm[:, :] = [40, 40, 40]
            self.player.show_dist_mark_ipm(self.ipm)

        if 'img_raw' in mess and mess['img_raw'] is not None:  # reuse img
            img = mess['img_raw'].copy()
            if not self.pause and ('ts' not in mess or self.ts_sync_local() - mess['ts'] > 5.0):
                self.player.show_failure(img, 'feed lost, check connection.')
        else:
            try:
                mess['img_raw'] = jpeg.decode(np.fromstring(mess['img'], np.uint8))
            except Exception as e:
                logger.error('img decode error:{}'.format(e))
                return
            img = mess['img_raw'].copy()

        misc_data = mess.get('misc')
        if misc_data:
            for source in list(mess['misc']):
                for entity in list(mess['misc'][source]):
                    self.draw_misc_data(img, mess['misc'][source][entity])

        frame_id = mess['frame_id']
        self.now_id = frame_id
        self.ts_now = mess['ts']
        self.player.ts_now = mess['ts']
        self.player.update_column_ts('video', mess['ts'])
        self.player.show_frame_id('video', frame_id)
        self.player.show_frame_cost(self.frame_cost)
        self.player.show_datetime(self.ts_now)

        if self.ts0 == 0:
            self.ts0 = self.ts_now

        # 如果有定位标签的话，渲染定位信息
        if self.vehicles['ego'].pinpoint:
            self.player.show_pinpoint(img, self.vehicles['ego'].pinpoint)

        for idx, source in enumerate(list(self.video_cache.keys())):
            if idx > 2:
                continue
            video = self.video_cache[source]
            self.video_cache[source]['updated'] = False
            video['device'] = source
            self.player.draw_img(video['img'], plugin_name='video-sub{}'.format(idx+1))
            self.player.show_video_info(video, plugin='video-sub{}'.format(idx+1))

        if not self.replay:
            self.player.show_version(img, self.cfg)
            if self.hub.fileHandler.is_recording:
                self.player.show_recording(img, self.hub.fileHandler.start_time)
                if self.hub.fileHandler.is_marking:
                    self.player.show_marking(img, self.hub.fileHandler.start_marking_time)
            else:
                self.player.show_recording(img, 0)

        else:
            self.player.show_replaying(self.ts_now - self.ts0)

        fps = self.player.cal_fps(frame_cnt)
        self.player.show_fps('video', fps)

        self.player.render_text_info(img)

        if img.shape[1] > 1280:
            fx = 1280 / img.shape[1]
            img = cv2.resize(img, None, fx=fx, fy=fx)
        if img.shape[0] > 960:
            fx = 960 / img.shape[0]
            img = cv2.resize(img, None, fx=fx, fy=fx)

        self.player.show_alarm_info(self.alarm_info)

        self.frame_cost = (time.time() - t0) * 0.1 + self.frame_cost * 0.9
        self.frame_drawn_cnt += 1
        self.frame_cost_total += self.frame_cost

        self.player.submit()
        return img

    def draw(self, frame_cnt):
        ts_ana = []
        draw_start_ts = time.time()
        img_aux = np.zeros([0, 427, 3], np.uint8)       # 其他视频图像显示块
        ts_ana.append(('draw start', draw_start_ts))

        # 解析主视频
        main_img = self.draw_img(self.player_cache['main'])
        ts_ana.append(('frame decode', time.time()))

        # 以主视频为基准
        self.ts_now = self.player_cache['main']['ts']
        self.player.ts_now = self.player_cache['main']['ts']
        self.player.update_column_ts('video', self.player_cache['main']['ts'])
        self.player.show_frame_id('video', self.player_cache['main']['frame_id'])
        self.player.show_frame_cost(self.frame_cost)        # 渲染画面的耗时
        self.player.show_datetime(self.ts_now)

        # CVE 启动时间
        if self.start_ts == 0:
            self.start_ts = self.player_cache['main']['ts']

        # 如果有定位标签的话，渲染定位信息
        if self.vehicles['ego'].pinpoint:
            self.player.show_pinpoint(main_img, self.vehicles['ego'].pinpoint)

        if self.show_ipm:
            # 显示俯视图
            self.m_g2i = self.transform.calc_g2i_matrix()

            if self.show_ipm_bg:
                self.ipm = cv2.warpPerspective(main_img, self.m_g2i, (self.transform.ipm_width, self.transform.ipm_height))
            else:
                self.ipm = np.zeros([self.transform.ipm_height, self.transform.ipm_width, 3], np.uint8)
                self.ipm[:, :] = [40, 40, 40]

            self.player.show_dist_mark_ipm(self.ipm)

        ts_ana.append(('prep ipm', time.time()))

        if 'x1_data' in self.player_cache['misc']:
            for data in self.player_cache['misc']['x1_data']:
                self.flow_player.draw(data, main_img)

        ts_ana.append(('pcv_data', time.time()))

        if not self.replay:
            self.player.show_version(main_img, self.cfg)
            if self.hub.fileHandler.is_recording:
                self.player.show_recording(main_img, self.hub.fileHandler.start_time)
                if self.hub.fileHandler.is_marking:
                    self.player.show_marking(main_img, self.hub.fileHandler.start_marking_time)
            else:
                self.player.show_recording(main_img, 0)
        else:
            self.player.show_replaying(self.player_cache['main']['ts'] - self.start_ts)

        fps = self.player.cal_fps(frame_cnt)
        self.player.show_fps('video', fps)

        # if not self.o_filter_q.empty():
        #     data = self.o_filter_q.get()
        #
        #     for i in data:
        #         signal, idx = i.split(".")
        #         if data[i] == 'filter':
        #             is_display = False
        #             if i not in self.filter:
        #                 self.filter.append(i)
        #         else:
        #             is_display = True
        #             if i in self.filter:
        #                 self.filter.remove(i)
        #
        #         for ip in self.hub.online:
        #             if int(idx) == self.hub.online[ip]['idx']:
        #                 for node in self.hub.online[ip]['ports']:
        #                     if self.hub.online[ip]['ports'][node].get('topic') == signal:
        #                         self.hub.online[ip]['ports'][node]['display'] = is_display
        #                     if self.hub.online[ip]['ports'][node].get('dbc') == signal:
        #                         self.hub.online[ip]['ports'][node]['display'] = is_display

        # 渲染状态框信息
        self.player.render_text_info(main_img)
        # 渲染提示信息
        self.show_alarm_info(main_img)
        
        # 渲染传感器数据
        misc_data = self.player_cache['misc']

        for i in self.filter:
            if misc_data.get(i):
                del(misc_data[i])

        if misc_data:
            for source in list(misc_data):
                for entity in list(misc_data[source]):
                    self.draw_misc_data(main_img, misc_data[source][entity])
        ts_ana.append(('misc_data', time.time()))
        main_img = self.resize_img(main_img)

        # 是否显示后视图像
        if self.sv_state == 'back':
            back_img = self.draw_img(self.player_cache['back'])
            if self.player_cache['back']['recv_first_img']:
                back_img = cv2.flip(back_img, 1)
                if misc_data:
                    for source in list(misc_data):
                        for entity in list(misc_data[source]):
                            if misc_data[source][entity].get('type') == 'obstacle' and misc_data[source][entity].get('sensor') in ['mu_rr', 'mu_rl', 'bosch_rl', 'bosch_rr', "ars_back"]:
                                self.player.show_obs(back_img, misc_data[source][entity], install_key=self.player_cache['back']['install'], y_mirror=True)
                self.player.show_video_info(back_img, self.player_cache['back'])

            back_img = self.resize_img(back_img)
            comb = np.vstack((main_img, back_img))
        else:
            comb = main_img
            # 对俯视图进行裁剪
            if self.show_ipm:
                self.ipm = self.ipm[:self.transform.ipm_front_height]

        # 是否显示俯视图
        if self.show_ipm:
            padding = np.zeros((comb.shape[0] - self.ipm.shape[0], self.ipm.shape[1], 3), np.uint8)
            comb = np.hstack((comb, np.vstack((self.ipm, padding))))
        else:
            # 显示其他视频
            for idx, source in enumerate(list(self.player_cache['videos'].keys())):
                if idx > 2:
                    continue
                video = self.player_cache['videos'][source]
                video['device'] = source

                self.player_cache['videos'][source]['updated'] = False
                img_small = cv2.resize(jpeg.decode(np.fromstring(video['img'], np.uint8)), (427, 240))

                self.player.show_video_info(img_small, video)
                img_aux = np.vstack((img_aux, img_small))
            ts_ana.append(('other frame decode', time.time()))

            padding = np.zeros((comb.shape[0] - img_aux.shape[0], img_aux.shape[1], 3), np.uint8)
            comb = np.hstack((comb, np.vstack((img_aux, padding))))

        self.frame_cost = (time.time() - draw_start_ts) * 0.1 + self.frame_cost * 0.9
        self.frame_drawn_cnt += 1
        self.frame_cost_total += self.frame_cost

        # t4 = time.time()
        ts_ana.append(('others', time.time()))

        return comb

    def draw_img(self, video_data):
        """
        绘制图像数据
        :param video_data:
        :return:
        """
        if not video_data:
            return

        # 视频图像 jpeg to raw
        try:
            if 'img_raw' in video_data and video_data['img_raw'] is not None:  # reuse img
                img = video_data['img_raw'].copy()
            else:
                try:
                    video_data['img_raw'] = jpeg.decode(np.fromstring(video_data['img'], np.uint8))
                except Exception as e:
                    logger.error("图片解码失败：{}".format(e))
                    return
                img = video_data['img_raw'].copy()
        except Exception as e:
            logger.error('img decode error:{}'.format(e))
            return

        # 是否掉线提示
        if not self.pause and ('ts' not in video_data or self.ts_sync_local() - video_data['ts'] > 5.0):
            self.player.show_failure(img, 'feed lost, check connection.')

        return img

    def save_rendered(self, img_rendered):
        if self.save_replay_video and self.replay:
            # print(comb.shape)
            if not self.vw:
                if isinstance(self.save_replay_video, str):
                    odir = self.save_replay_video
                else:
                    odir = os.path.dirname(self.rlog)
                self.vw = VideoRecorder(odir, fps=20)
                self.vw.set_writer("replay-render", img_rendered.shape[1], img_rendered.shape[0])
                print('--------save replay video', odir)
            self.vw.write(img_rendered)

    def draw_rtk(self, img, data):
        if len(data) == 0 or data.get('source') is None:
            return

        if len(self.rtk_pair[0]) > 0 and len(self.rtk_pair[1]) > 0:
            self.player.show_target(img, self.rtk_pair[1], self.rtk_pair[0])
            if self.show_ipm:
                self.player.show_ipm_target(self.ipm, self.rtk_pair[1], self.rtk_pair[0])

    def update_pinpoint(self, data):
        if data['type'] == 'pinpoint':
            self.vehicles['ego'].set_pinpoint(data)
            if not self.replay:
                self.hub.fileHandler.insert_raw(
                    (data['ts'], data.get('source') + '.pinpoint', compose_from_def(ub482_defs, data)))
            # print('insert pinpoint:', data)
            return

    def draw_rtk_ub482(self, img, data):
        self.player.show_ub482_common(img, data)
        source = data.get('source')
        role = self.hub.get_veh_role(source)

        if data['type'] == 'inspva' or data['type'] == 'pinpoint':
            if self.set_pinpoint or data['type'] == 'pinpoint':
                self.set_pinpoint = False
                pp = data.copy()
                pp['type'] = 'pinpoint'
                self.update_pinpoint(pp)
                if not self.replay:
                    self.hub.fileHandler.pinpoint = pp
            data['hor_speed'] = (data.get("vel_n")**2 + data.get("vel_e")**2)**0.5
            data['trk_gnd'] = atan2(data.get("vel_e"), data.get("vel_n"))
        self.vehicles[role].update_dynamics(data)

        if role in ('ego', 'default'):
            if 'lat' in data:
                if self.set_pinpoint:
                    self.set_pinpoint = False
                    pp = data.copy()
                    pp['type'] = 'pinpoint'
                    self.update_pinpoint(pp)
                    if not self.replay:
                        self.hub.fileHandler.pinpoint = pp
                if self.gga is None and self.en_gga and not self.replay:
                    server = self.cfg.runtime['modules']['GGA_reporter']['ntrip_address']
                    port = self.cfg.runtime['modules']['GGA_reporter']['port']
                    self.gga = GGAReporter(server, port)
                    self.gga.start()
                if self.gga is not None and not self.replay:
                    self.gga.set_pos(data['lat'], data['lon']) if data['pos_type'] != 'NONE' else None
                    if data['pos_type'] != 'NONE':
                        self.statistics['GGA_report_coord'] = 'Lat:{lat:.8f}  Lon:{lon:.8f}  Hgt:{hgt:.3f}'.format(
                            **data)
            elif 'yaw' in data:
                self.player.show_heading_horizen(img, data)
        else:  # other vehicle
            if self.vehicles['ego']:
                target = get_rover_target(self.vehicles['ego'], self.vehicles[role])
                # print(target)
                if target:
                    self.player.show_rtk_target(img, target)
                    if self.show_ipm:
                        self.player.show_rtk_target_ipm(self.ipm, target)

        pp_target = self.vehicles['ego'].get_pp_target(data)
        # print("target:", pp_target)
        if pp_target:

            # t0 = time.time()
            self.player.show_rtk_target(img, pp_target)
            if self.show_ipm:
                self.player.show_rtk_target_ipm(self.ipm, pp_target)

    def viz_rtcm(self, img, data):
        # if data['type'] == 'rtcm':
        #     print(data)
        if data['id'] == 1005:
            llh = PosVector(data['ECEF-X'], data['ECEF-Y'], data['ECEF-Z']).ToLLH()
            data['lat'] = llh.lat
            data['lon'] = llh.lon
            data['hgt'] = llh.alt
            self.player.show_rtcm(data)
            print('station loc:', data['lat'], data['lon'])

    def process_tsr(self, img, data):
        ego_pose = self.vehicles['ego'].get_pos()
        if not ego_pose:
            print('no pose when process tsr')
            return
        ego_blh = np.array([ego_pose['lat'], ego_pose['lon'], ego_pose['hgt']])
        ego_atti = np.array([ego_pose['yaw'], 0, 0])
        target = np.array(
            [data['pos_lat'], data['pos_lon'], data['pos_hgt']])  # target position in (right, front, up) order
        lat, lon, hgt = body2blh(ego_blh, ego_atti, target)
        # self.vehicles['ego'].set_pinpoint({'type': 'pinpoint', 'ts': data['ts'], 'source': data['source'], 'lat': lat, 'lon': lon, 'hgt': hgt})
        # print(lat, lon, hgt, 'ego yaw:', ego_pose['yaw'], data)
        self.player.show_tsr(img, data)

    def handle_calib_param(self, data):
        r = {data['source']: {'pitch': data['camera_pitch'], 'roll': data['camera_roll'], 'yaw': data['camera_yaw'],
                              'fu': data['camera_fov_w'], 'fv': data['camera_fov_h'], 'cu': data['camera_cu'],
                              'cv': data['camera_cv'], 'height': data['camera_height'],
                              'lon_offset': -data['front_dist_to_camera'],
                              'lat_offset': 0.5 * (data['left_dist_to_camera'] - data['right_dist_to_camera'])}}
        self.cfg.installs.update(r)
        self.hub.fileHandler.d['installs'] = self.cfg.installs

    def handle_calib_params(self, data):
        r = {data['source']: {'pitch': -data['pitch'], 'roll': -data['roll'], 'yaw': -data['yaw'],
                              'fu': data['fu'], 'fv': data['fv'], 'cu': data['cu'],
                              'cv': data['cv'], 'height': data['height'],
                              'lon_offset': data['front_vehicle_edge_dist'],
                              'lat_offset': 0.5 * (data['left_vehicle_edge_dist'] - data['right_vehicle_edge_dist'])}}
        self.cfg.installs.update(r)
        self.hub.fileHandler.d['installs'] = self.cfg.installs
        self.hub.fileHandler.save_param()

    def specific_handle(self, img, data):
        src = data.get('source')
        if not src:
            return
        # if 'rtk' in src:
        #     self.calib_data['rtk'] = data
        if 'esr' in src:
            # if data['id'] == 3:
            #     print(data)
            if 'rtk' in self.calib_data and is_near(self.calib_data['rtk'], data):
                d_azu = self.calib_data['esr']['angle'] - data['angle'] if 'esr' in self.calib_data else 0
                self.calib_data['esr'] = data
                # print(self.calib_data['esr'])
                if fabs(d_azu) > 0.01:
                    self.calib_data['esr']['valid'] = False
                else:
                    self.calib_data['esr']['valid'] = True
        if 'rtk.target' in src:
            self.calib_data['rtk'] = data
            # print(self.calib_data['rtk'])

        # if data['source'] == 'rtk.2' and data['velN']**2 + data['velE']**2 + data['velD']**2 < 0.001:
        #     self.calib_esr()

    def analyze_profile(self, img, data):
        if self.to_web:
            self.o_msg_q.put(('profiling', data))

    def draw_misc_data(self, img, data, install_key="video"):
        if 'type' not in data:
            return

        # todo:待优化
        role = self.hub.get_veh_role(data.get('source'))
        if role not in self.vehicles:
            self.vehicles[role] = Vehicle(role)

        if data.get("status_show"):
            self.player.show_status_info(data.get("source"), data["status_show"])

        if data['type'] == 'pcv_data':
            if self.replay or (not self.replay and self.draw_algo):
                for t in data["data"]:
                    self.flow_player.draw(t, img)
        elif data["type"] == "status":
            self.player.update_column_ts(data.get('source'), data.get('ts'))
        elif data['type'] == 'obstacle':
            self.player.show_obs(img, data, install_key=install_key)
            self.player.update_column_ts(data.get('source'), data.get('ts'))
            if self.show_ipm:
                self.player.show_ipm_obs(self.ipm, data)
            if data.get('cipo'):
                self.cipv = data
        # lane 车道线
        elif data['type'] == 'lane':
            self.player.draw_lane_r(img, data)
            if self.show_ipm:
                self.player.draw_lane_ipm(self.ipm, data)
        # vehicle 车辆信息
        elif data['type'] == 'vehicle_state':
            self.player.draw_vehicle_state(img, data)
            self.player.update_column_ts(data['source'], data['ts'])

        elif data['type'] == 'CIPV':
            self.cipv = data

        elif data['type'] == 'rtk':
            data['updated'] = True
            self.draw_rtk(img, data)
            # print('------------', data['type'], data)

        elif data['type'] in ['bestpos', 'heading', 'bestvel', 'pinpoint']:
            self.draw_rtk_ub482(img, data)
            self.player.update_column_ts(data['source'], data['ts'])
        elif data['type'] == 'rtcm':
            self.viz_rtcm(img, data)
        elif data['type'] == 'gps':
            # print('gps ts:', data['ts'])
            self.player.show_gps(data)
            self.player.update_column_ts(data['source'], data['ts'])
        elif data['type'] == 'traffic_sign':
            # print(data)
            self.process_tsr(img, data)
            # self.player.show_tsr(img, data)
            # self.pause = True
        elif data['type'] == 'warning':
            self.player.show_warning(img, data)
        elif data['type'] == 'profiling':
            self.analyze_profile(img, data)
        elif data['type'] in ['inspva', 'drpva', 'pashr', 'gpgga']:
            self.player.show_rtk_pva(img, data)
            self.player.show_heading_horizen(img, data)
        elif data['type'] == 'calib_param':
            self.handle_calib_param(data)
        elif data['type'] == 'calib_params':
            self.handle_calib_params(data)
        self.specific_handle(img, data)
        return True

    def handle_keyboard(self):
        """
        获取视频窗口的按键事件
        :return:
        """
        if self.eclient:
            pass
            # key = BaseDraw.get_event()
            # if key and len(key) == 1:
            #     key = ord(key)
            #     self.control(key)
        else:
            key = cv2.waitKey(1) & 0xFF
            self.control(key)

    def control(self, key):
        """
        按键事件方法
        :param key:
        :return:
        """
        if key == ord('q') or key == 27:
            if not self.to_web:
                cv2.destroyAllWindows()
                if self.vw is not None:
                    self.vw.release()
            self.exit = True
        elif key == ord('['):
            if self.pause and self.replay:
                self.cache_pause_idx -= 1
                self.cache_pause_idx = max(self.cache_pause_idx, 1)
                self.cache = copy.deepcopy(self.cache_pause_data[self.cache_pause_idx-1])

        elif key == ord(']'):
            if self.pause and self.replay:
                self.cache_pause_idx += 1
                self.cache_pause_idx = min(self.cache_pause_idx, self.cache_pause_max_len)
                self.cache = copy.deepcopy(self.cache_pause_data[self.cache_pause_idx-1])

        elif key == 32:  # space
            # 如果是回放的话空格键是控制暂停\播放，否则是语音打点记录功能
            if self.replay:
                self.pause = not self.pause
                logger.debug('Pause: {}'.format(self.pause))
                if self.pause:
                    self.pause_t = time.time()
                    self.hub.pause(True)
                else:
                    paused_t = time.time() - self.pause_t
                    self.hub.add_pause(paused_t)
            else:
                from recorder.voice_note import Audio

                if self.audio is None or not self.audio.is_alive():
                    self.audio = None
                    dur_time = 15
                    if self.hub.fileHandler.is_recording:
                        file_path = os.path.join(self.hub.fileHandler.path, "waves", "%d.wav" % self.wav_cnt)
                        self.audio = Audio(file_path, is_replay=False, duration_time=dur_time)
                        self.audio.start()
                        self.hub.fileHandler.insert_raw((self.ts_now, "voice_note", str(self.wav_cnt)))
                        self.wav_cnt += 1
                        self.alarm_info["voice_note"] = time.time() + dur_time

        elif key == ord('r'):   # 录制功能
            if self.replay:
                return

            if self.hub.fileHandler.is_recording:
                self.stop_rec()
                self.hub.parse_can_msgs(self.parse_state)

            else:
                self.start_rec()
                if self.cfg.runtime.get('low_profile'):
                    self.hub.parse_can_msgs(False)
            logger.warning('toggle recording status: {}'.format(self.hub.fileHandler.is_recording))
        elif key == ord('0'):
            if self.hub.fileHandler.is_recording:
                if self.hub.fileHandler.is_marking:
                    self.hub.fileHandler.end_mark()
                else:
                    self.hub.fileHandler.start_mark()
        elif key == ord('p'):
            self.set_pinpoint = True
            # print(self.set_target)
        elif key == ord('c'):
            self.calib_esr()
        elif key == ord('b'):
            self.show_ipm_bg = not self.show_ipm_bg
        elif key == ord('i'):
            self.show_ipm = not self.show_ipm
        elif key == ord('f'):
            status = next(self.sideview_state)
            if status == self.sv_state:
                status = next(self.sideview_state)
            self.sv_state = status
        elif key == ord('2'):
            print('add time.')
            self.enable_auto_interval_adjust = False
            self.display_interval = self.display_interval + 0.005
        elif key == ord('1'):
            print('decrease time.')
            self.enable_auto_interval_adjust = False
            self.display_interval = self.display_interval - 0.005
        elif key == ord('t'):
            self.parse_state = not self.parse_state
            self.hub.parse_can_msgs(self.parse_state)

    def start_rec(self):
        self.hub.fileHandler.start_rec(self.rlog)
        pp = self.vehicles['ego'].pinpoint
        if pp and not self.replay:
            logger.debug("已打过定位标签，进行续记录：{}".format(pp))
            self.hub.fileHandler.insert_raw(
                (pp['ts'], pp.get('source') + '.pinpoint', compose_from_def(ub482_defs, pp)))

    def stop_rec(self):
        self.hub.fileHandler.stop_rec()

    def left_click(self, event, x, y, flags, param):
        # print(event, x, y, flags, param)
        if cv2.EVENT_LBUTTONDOWN == event:
            logger.debug('left btn down {} {}'.format(x, y))

    def check_status(self):
        """
        检查信号接收情况
        :return:
        """
        if self.hub.mq.full():
            self.stuck_cnt += 1
        else:
            self.stuck_cnt = 0

        main_cache = self.player_cache['main'].copy()
        videos_cache = self.player_cache['videos'].copy()
        # main video ts
        # all_ts = [main_cache['ts']]
        source_list = [{"source": "main", 'ts': main_cache['ts']}]
        # other video ts
        for source in videos_cache:
            d = videos_cache[source]
            if type(d) == dict and 'ts' in d:
                # all_ts.append(d['ts'])
                source_list.append({"source": d['source'], 'ts': d['ts']})

        # 收集其他信号的接收时间
        for source in self.player_cache['misc']:
            for key in self.player_cache['misc'][source]:
                d = self.player_cache['misc'][source][key]
                if type(d) == dict and 'ts' in d:
                    # all_ts.append(d['ts'])
                    source_list.append({"source": d['source'], 'ts': d['ts']})

        source_list = sorted(source_list, key=lambda x: x["ts"])
        dt = source_list[-1]['ts'] - source_list[0]['ts']
        # dt = np.ptp(all_ts)

        # 出现超时信号进行处理
        if dt > 5:
            now = time.time()
            if now - self.record_time_not_sync > 60:
                self.record_time_not_sync = now
                logger.warning("time_not_sync:{} max:{} min:{}".format(dt, source_list[-1], source_list[0]))
            self.alarm_info["time_not_sync"] = now + 3

            return {'status': 'fail', 'info': 'collectors\' time not aligned!'}
        return {'status': 'ok', 'info': 'oj8k'}

    def check_signal(self, msg, signal_list):
        # 初始化msg信息
        for device in msg:
            for node in msg[device]['ports']:
                if msg[device]['ports'][node]['enable'] is not False:
                    msg[device]['ports'][node]['enable'] = True

        """
        通过信号有无检测设备状态
        """
        for device in msg:
            # can signal
            if msg[device]['type'] == 'can_collector':
                for i in signal_list:
                    ip, port, idx, source = i[0], i[1], i[2], i[3]
                    if ip == msg[device]['ip'] and port == msg[device]['port'] and idx == msg[device]['idx'] \
                            and isinstance(source, list):
                        for s in source:
                            can = s.split('.')[2]
                            if can in msg[device]['ports']:
                                msg[device]['ports'][can]['enable'] = 'running'

            # other signal
            else:
                for i in signal_list:
                    ip, port, idx, source = i[0], i[1], i[2], i[3]
                    if ip == msg[device]['ip'] and idx == msg[device]['idx']:
                        for node in msg[device]['ports']:
                            if port == msg[device]['ports'][node]['port']:
                                msg[device]['ports'][node]['enable'] = 'running'

        return msg

    def send_online_devices(self):
        if not self.to_web:
            return

        msg = self.hub.online

        # if self.hub.sq.full():
        #     self.stuck_cnt += 1
        # else:
        #     self.stuck_cnt = 0
        #
        # signal_list = []
        # while not self.hub.sq.empty():
        #     sq = self.hub.sq.get()
        #     if sq not in signal_list:
        #         signal_list.append(sq)
        #
        # msg = self.check_signal(msg, signal_list)

        time.sleep(2)
        # self.vs.ws_send('devices', msg)
        if self.o_msg_q and not self.o_msg_q.full():
            self.o_msg_q.put(('devices', msg))
        # print('sent online devices')
        return {'status': 'ok', 'info': 'oj8k'}

    def send_statistics(self):
        if not self.to_web:
            return

        self.statistics['cpu_mem_info'] = 'cpu_used: {}% mem_used {}% cpu_temp: {}c'.format(get_cpu_pct(),
                                                                                            get_mem_pct(),
                                                                                            get_cpu_temp())

        for item in self.statistics:
            self.o_msg_q.put(('delay', {'name': item, 'value': '{}'.format(self.statistics[item])}))
        # self.web_img['now_image'] = comb.copy()
        # self.o_msg_q.put(('delay', {'name': 'frame_popping_cost', 'delay': '{:.1f}'.format(1000 * (t2 - t1))}))
        # self.o_msg_q.put(('delay', {'name': 'frame_caching_cost', 'delay': '{:.1f}'.format(1000 * (t1 - t0))}))
        # self.o_msg_q.put(
        #     ('delay', {'name': 'refreshing_rate', 'delay': '{:.1f}'.format(1.0 / self.display_interval)}))

    def calib_esr(self, ofile='esr_clb.txt'):
        if 'rtk' not in self.calib_data:
            print('no rtk data for calibration.')
            return

        if 'esr' not in self.calib_data:
            print('no esr data for calibration.')
            print(self.calib_data['rtk'])
            return
        dt = self.calib_data['rtk']['ts'] - self.calib_data['esr']['ts']
        if dt > 1.0:
            print('esr and rtk time diff too large.', dt, self.calib_data['rtk'])
            return

        if not self.calib_data['esr'].get('valid'):
            print('esr calib data not valid.')
            return

        azu_rtk = self.calib_data['rtk']['angle']
        azu_esr = self.calib_data['esr']['angle']
        d_azu = azu_rtk - azu_esr
        ts = self.calib_data['rtk']['ts']
        print('azu diff from rtk to esr:', d_azu, azu_rtk)
        with open(ofile, 'a') as cf:
            tv_s = int(ts)
            tv_us = (ts - tv_s) * 1000000
            data = '{} {} {} {} {}'.format(self.now_fid, d_azu, azu_rtk, azu_esr, dt)
            log_line = "%.10d %.6d " % (tv_s, tv_us) + 'esr.calib' + ' ' + data + "\n"
            cf.write(log_line)


if __name__ == "__main__":
    pass

    # local_path = os.path.split(os.path.realpath(__file__))[0]
    # # print('local_path:', local_path)
    # os.chdir(local_path)
    #
    # if len(sys.argv) == 1:
    #     sys.argv.append('config/cfg_lab.json')
    #
    # if '--direct' in sys.argv:
    #     print('direct mode.')
    #     hub = Hub(direct_cfg=sys.argv[2])
    #     pcc = PCC(hub, ipm=True, replay=False)
    #     pcc.start()
    #
    # elif '--headless' in sys.argv:
    #     print('headless mode.')
    #     hub = Hub(headless=True)
    #     hub.start()
    #     pcc = HeadlessPCC(hub)
    #
    #     t = dThread(target=pcc.start)
    #     t.start()
    #     # hub.fileHandler.start_rec()
    #     # pcc.start()
    #
    #     from tornado.web import Application, RequestHandler, StaticFileHandler
    #     from tornado.ioloop import IOLoop
    #
    #
    #     class IndexHandler(RequestHandler):
    #         def post(self):
    #             action = self.get_body_argument('action')
    #             if action:
    #                 if 'start' in action:
    #                     if not hub.fileHandler.recording:
    #                         hub.fileHandler.start_rec()
    #                         print(hub.fileHandler.recording)
    #                         self.write({'status': 'ok', 'action': action, 'message': 'start recording'})
    #                     else:
    #                         self.write({'status': 'ok', 'message': 'already recording', 'action': action})
    #                 elif 'stop' in action:
    #                     if not hub.fileHandler.recording:
    #                         self.write({'status': 'ok', 'message': 'not recording', 'action': action})
    #                     else:
    #                         hub.fileHandler.stop_rec()
    #                         print(hub.fileHandler.recording)
    #                         self.write({'status': 'ok', 'action': action, 'message': 'stop recording'})
    #                 elif 'check' in action:
    #                     mess = 'recording' if hub.fileHandler.recording else 'not recording'
    #                     self.write({'status': 'ok', 'action': action, 'message': mess})
    #                 elif 'image' in action:
    #                     img = hub.fileHandler.get_last_image()
    #                     img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
    #                     if img is None:
    #                         # print('pcc', img)
    #                         # img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
    #                         img = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)
    #
    #                     base64_str = cv2.imencode('.jpg', img)[1].tostring()
    #                     base64_str = base64.b64encode(base64_str).decode()
    #                     self.write({'status': 'ok', 'action': action, 'message': 'get image', 'data': base64_str})
    #                 else:
    #                     self.write({'status': 'ok', 'message': 'unrecognized action', 'action': action})
    #             else:
    #                 # self.hub.fileHandler.stop_rec()
    #                 self.write({'status': 'error', 'message': 'not action', 'action': None})
    #
    #         def get(self):
    #             self.render("web/index.html")
    #
    #
    #     app = Application([
    #         (r'/', IndexHandler),
    #         (r"/static/(.*)", StaticFileHandler, {"path": "web/statics"}),
    #     ], debug=False)
    #     app.listen(9999)
    #     IOLoop.instance().start()
    #
    # else:
    #     print('normal mode.')
    #     uni_conf = load_cfg(sys.argv[1])
    #     hub = Hub()
    #     pcc = PCC(hub, ipm=False, replay=False)
    #     pcc.start()
    #
    # # pcc = PCC(hub, ipm=True, replay=False)
    # # pcc.start()
