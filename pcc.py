#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

import base64
import logging
import time
from datetime import datetime
from math import fabs
from multiprocessing import Manager
from multiprocessing.dummy import Process as Thread
import signal
import cv2
import sys
import numpy as np
# from turbojpeg import TurboJPEG

from config.config import local_cfg, load_cfg
from net.ntrip_client import GGAReporter
from player import FlowPlayer
from player.pcc_ui import Player
from recorder import VideoRecorder
from recorder.convert import *
from sink.hub import Hub
from tools.geo import *
from tools.match import is_near
# from tools.mytools import Supervisor
from tools.transform import Transform, OrientTuner
from tools.vehicle import Vehicle, get_rover_target
from tools.cpu_mem_info import *
from multiprocessing import Queue


# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

#sample_jpg = open('/home/nan/workshop/git/pcview/static/img/no_video.jpg', 'rb').read()

def loop_traverse(items):
    while True:
        for item in items:
            yield item


class PCC(Thread):
    def __init__(self, hub, replay=False, rlog=None, ipm=None, save_replay_video=None, uniconf=None, to_web=None,
                 auto_rec=False):
        super(PCC, self).__init__()
        # from config.config import runtime
        self.hub = hub
        self.cfg = uniconf
        self.player = Player(uniconf)
        self.exit = False
        self.pause = False
        # self.recording = False
        self.replay = replay
        self.rlog = rlog
        self.frame_idx = 0
        self.ts0 = 0

        self.now_id = 0
        # self.pre_rtk = {}
        self.ts_now = 0
        self.cipv = {}
        # self.msg_cnt = {}
        self.transform = Transform(uniconf)
        self.m_g2i = self.transform.calc_g2i_matrix()
        self.ipm = None
        self.show_ipm = ipm
        self.set_pinpoint = False
        self.target = None
        self.rtk_pair = [{}, {}]
        self.ot = OrientTuner(uniconf)
        self.show_ipm_bg = False
        self.auto_rec = auto_rec

        self.refresh_rate = 20
        if uniconf.runtime.get('low_profile'):
            self.refresh_rate = 5
        self.display_interval = 1.0 / self.refresh_rate
        self.vehicles = {'ego': Vehicle('ego')}
        self.calib_data = dict()
        self.frame_cost = 0
        self.frame_cost_total = 0
        self.frame_drawn_cnt = 0
        self.video_cache = {}
        self.cache = {}
        self.init_cache()
        self.run_cost = 0.05
        self.stuck_cnt = 0
        self.statistics = {}
        self.enable_auto_interval_adjust = True
        self.parse_state = True
        # self.jpeg_dec = TurboJPEG()

        # cv2.resizeWindow('adj', 600, 600)
        self.sideview_state = loop_traverse(['ipm', 'video_aux'])
        self.sv_state = 'ipm'
        # self.rt_param = self.cfg.runtime
        # cv2.namedWindow('video_aux')

        # cv2.createTrackbar('ESR_y', 'adj', 500, 1000, self.ot.update_esr_yaw)

        if replay:
            self.hub.d = Manager().dict()

            def update_speed(x):
                self.hub.d['replay_speed'] = 1 if x // 10 < 1 else x // 10
                print('replay-speed is', self.hub.d['replay_speed'])

            if not to_web:
                cv2.createTrackbar('replay-speed', 'adj', 10, 50, update_speed)

        self.gga = None
        if not self.replay:
            self.en_gga = self.cfg.runtime['modules']['GGA_reporter']['enable']
        else:
            self.en_gga = False
        self.flow_player = FlowPlayer()

        self.save_replay_video = save_replay_video
        self.vw = None
        self.vs = None
        if not to_web:
            self.to_web = False
            cv2.namedWindow('MINIEYE-CVE')
            cv2.setMouseCallback('MINIEYE-CVE', self.left_click, '1234')
            cv2.namedWindow('adj')
            cv2.createTrackbar('Yaw  ', 'adj', 500, 1000, self.ot.update_yaw)
            cv2.createTrackbar('Pitch', 'adj', 500, 1000, self.ot.update_pitch)
            cv2.createTrackbar('Roll  ', 'adj', 500, 1000, self.ot.update_roll)
        else:
            self.to_web = True
            # from video_server import VideoServer
            import video_server
            # self.web_img = video_server.server_dict
            # self.ctrl_q = video_server.ctrl_q
            self.o_msg_q = video_server.msg_q
            self.o_img_q = video_server.img_q
            # video_server.local_path = uniconf.local_cfg.log_root
            self.vs = to_web
            # self.vs.start()

        # if self.save_replay_video and self.replay:
        #     self.vw = VideoRecorder(os.path.dirname(self.rlog), fps=20)
        #     self.vw.set_writer("replay-render", 1760, 720)
        #     print('--------save replay video', os.path.dirname(self.rlog))

        # def exit_for_signal(signal_num, frame):
        #     if self.vs:
        #         self.vs.terminate()
        #     print("exit by signal")
        #     sys.exit(0)
        # for sig in [signal.SIGINT, signal.SIGTERM]:
        #     signal.signal(sig, exit_for_signal)

    def init_cache(self):
        self.cache.clear()
        self.cache['misc'] = {}
        self.cache['info'] = {}
        self.cache['ts'] = 0
        self.cache['img'] = open('static/img/no_video.jpg', 'rb').read()
        self.cache['img_raw'] = cv2.imdecode(np.fromstring(self.cache['img'], np.uint8), cv2.IMREAD_COLOR)
        self.cache['frame_id'] = 0

    def clean_cache(self):
        try:
            ts_now = time.time()
            for source in list(self.cache['misc']):
                for entity in list(self.cache['misc'][source]):
                    ts_a = self.cache['misc'][source][entity].get('ts_arrival')
                    if not ts_a or ts_now - ts_a > max(3 * self.display_interval, 0.4):
                        del self.cache['misc'][source][entity]
        except Exception as e:
            print('error when clean cache:', entity)
            pass

    def cache_data(self, d):
        if not d:
            return
        fid, data, source = d
        # if 'type' not in data:
        #     print(data)
        if source not in self.cache['misc']:
            self.cache['misc'][source] = {}
            self.cache['info'][source] = {}
        if isinstance(data, list):
            # print('msg data list')
            for d in data:
                dtype = d.get('type') if 'type' in d else 'notype'
                id = str(d.get('id')) if 'id' in d else 'noid'
                entity = dtype + '.' + id
                # if d['type'] in ['bestpos', 'heading', 'bestvel', 'pinpoint']:
                #     print(entity, '-------------------------------------')
                self.cache['misc'][source][entity] = d
                self.cache['info'][source]['integrity'] = 'framed'
        elif isinstance(data, dict):
            # print(data)
            if 'video' in data['type']:
                is_main = data.get('is_main')
                # if not self.replay:
                    # self.hub.fileHandler.insert_jpg(
                    #     {'ts': data['ts'], 'frame_id': data['frame_id'], 'jpg': data['img'],
                    #      'source': 'video' if is_main else data['source']})
                if not is_main:
                    if data['source'] not in self.video_cache:
                        self.video_cache[data['source']] = {}
                    # data['img_raw'] = cv2.imdecode(np.fromstring(data['img'], np.uint8), cv2.IMREAD_COLOR)
                    self.video_cache[data['source']] = data
                    self.video_cache[data['source']]['updated'] = True

                else:
                    self.cache['img'] = data['img']
                    self.cache['img_raw'] = None
                    try:
                        pass
                        # self.cache['img_raw'] = cv2.imdecode(np.fromstring(data['img'], np.uint8), cv2.IMREAD_COLOR)
                        # self.o_img_q.put(data['img'])
                    except Exception as e:
                        print('img decode error:', e)
                        return
                    self.cache['frame_id'] = fid
                    self.cache['ts'] = data['ts']
                    self.cache['updated'] = True
                    return True
            else:
                dtype = data.get('type') if 'type' in data else 'notype'
                id = str(data.get('id')) if 'id' in data else 'noid'
                entity = data['source'] + '.' + dtype + '.' + id
                self.cache['misc'][source][entity] = data
                self.cache['info'][source]['integrity'] = 'divided'

    def adjust_interval(self):
        if not self.enable_auto_interval_adjust:
            return
        iqsize = self.hub.msg_queue.qsize()
        self.statistics['pcc_inq_size'] = iqsize
        if iqsize > 300:
            self.display_interval = max(self.display_interval, self.run_cost) + 0.005
        elif iqsize < 1 and self.run_cost < self.display_interval:
            self.display_interval = self.display_interval - 0.005
        else:
            return {'status': 'ok'}
        if self.cfg.runtime.get('low_profile'):
            ll = 0.2
        else:
            ll = 0.05

        if self.display_interval > 1.0:
            self.display_interval = 1.0
        elif self.display_interval < ll:
            self.display_interval = ll
        print('refresh interval set to', self.display_interval, 'hub qsize:', iqsize)
        return {'status': 'ok'}

    def run(self):
        # self.hub.start()
        self.player.start_time = datetime.now()
        frame_cnt = 0
        data_cnt = 0
        last_ts = time.time()
        print('entering pcc loop. pid', os.getpid())

        while not self.exit:
            if not self.hub.is_alive() and self.replay:
                print('hub exit running.')
                print('average frame cost: {:.1f}ms'.format(
                    1000 * self.frame_cost_total / self.frame_drawn_cnt)) if self.frame_drawn_cnt != 0 else None
                return
            t0 = time.time()
            # d = self.hub.pop_simple()  # receive
            try:
                d = self.hub.pop_common()
                if not d:
                    continue
                t1 = time.time()

                new_frame = self.cache_data(d)
                if new_frame:
                    frame_cnt += 1
                    if frame_cnt > 500:
                        self.player.start_time = datetime.now()
                        frame_cnt = 1

                t2 = time.time()
                if not self.replay:
                    qsize = self.hub.fileHandler.log_q.qsize()
                    self.statistics['fileHandler_log_q_size'] = qsize
                #     # print('raw queue size:', qsize)
                #     if self.hub.fileHandler.is_recording and qsize > 2000:
                #         print('msg_q critical, skip drawing.', qsize)
                #         # time.sleep(0.1)
                #         continue
                #     iqsize = self.hub.msg_queue.qsize()
                #     if iqsize > 2000:
                #         # print('iqsize:', iqsize, '>1000. pop cost: {:.2f}ms'.format((t1-t0)*1000), d[2], sys.getsizeof(d[1]))
                #         # self.adjust_interval()
                #         continue
            except Exception as e:
                print('pcc run error:', e)
                raise e
                continue


            # render begins
            if time.time() - last_ts > self.display_interval:
                self.handle_keyboard()
                # time.sleep(0.001)
                # print('wait to refresh', self.display_interval)
                last_ts = time.time()
                # if not self.replay:
                #     self.hub.parse_can_msgs()
                if not self.replay and self.statistics['fileHandler_log_q_size'] > 10000:
                    show = False
                else:
                    show = True
                self.render(frame_cnt, show)

            t4 = time.time()

            self.statistics['frame_popping_cost'] = '{:.2f}'.format(1000 * (t1 - t0))
            self.statistics['frame_caching_cost'] = '{:.2f}'.format(1000 * (t2 - t1))
            self.statistics['frame_rendering_cost'] = '{:.2f}'.format(1000 * (t4 - t2))
            self.statistics['refreshing_rate'] = '{:.1f}'.format(1.0 / self.display_interval)
            # print('pcc time cost:popping:{:.2f}ms caching:{:.2f}ms rendering:{:.2f}ms total:{:.2f}ms iqsize:{}'.format(
            #     1000 * (t1 - t0), 1000 * (t2 - t1), 1000 * (t4 - t2), 1000 * (t4 - t0), self.hub.msg_queue.qsize()), d[2])
            self.run_cost = self.run_cost * 0.9 + (t4 - t0) * 0.1

    def render(self, frame_cnt, show=True):
        if show:
            img_rendered = self.draw(self.cache, frame_cnt)  # render
            # ts_render = time.time()
            if self.to_web:
                # self.web_img['now_image'] = comb.copy()
                # self.o_msg_q.put(
                #     ('delay', {'name': 'frame_render_cost', 'delay': '{:.1f}'.format(self.frame_cost * 1000)}))
                self.statistics['frame_total_cost'] = '{:.2f}ms'.format(self.frame_cost * 1000)
                if not self.o_img_q.full():
                    self.o_img_q.put(img_rendered)
            else:
                cv2.imshow('MINIEYE-CVE', img_rendered)

            self.save_rendered(img_rendered)
        t3 = time.time()

        while self.replay and self.pause:
            self.handle_keyboard()
            self.draw(self.cache, frame_cnt)
            self.hub.pause(True)
            time.sleep(0.1)

        self.clean_cache()

        if self.replay:
            self.hub.pause(False)
            if self.hub.d:
                frame_cnt += self.hub.d['replay_speed'] - 1
                # print(frame_cnt)
        # self.draw(d, frame_cnt)

        # time.sleep(0.01)

        if self.auto_rec:
            self.auto_rec = False
            self.start_rec()

    def draw(self, mess, frame_cnt):
        # print(mess[''])
        ts_ana = []
        t0 = time.time()
        ts_ana.append(('draw start', t0))

        try:
            if 'img_raw' in mess and mess['img_raw'] is not None:
                img = mess['img_raw'].copy()
                # print('reuse video.')
            else:
                # return
                mess['img_raw'] = cv2.imdecode(np.fromstring(mess['img'], np.uint8), cv2.IMREAD_COLOR)
                # mess['img_raw'] = self.jpeg_dec.decode(mess['img'])
                img = mess['img_raw'].copy()
        except Exception as e:
            print('img decode error', mess)
            # raise e
            return
        # ts_fdec = time.time()
        ts_ana.append(('frame decode', time.time()))

        frame_id = mess['frame_id']
        self.now_id = frame_id
        self.ts_now = mess['ts']
        self.player.ts_now = mess['ts']
        self.player.update_column_ts('video', mess['ts'])
        # print(mess)
        # print(frame_id, img.shape)

        if self.ts0 == 0:
            self.ts0 = self.ts_now

        # if not self.replay and mess.get('updated'):
        #     self.hub.fileHandler.insert_video(
        #         {'ts': mess['ts'], 'frame_id': frame_id, 'img': mess['img_raw'], 'source': 'video'})

        # self.player.show_columns(img)
        if self.vehicles['ego'].dynamics.get('pinpoint'):
            self.player.show_pinpoint(img, self.vehicles['ego'].dynamics['pinpoint'][0])
        self.player.show_frame_id(img, 'video', frame_id)
        self.player.show_frame_cost(self.frame_cost)
        self.player.show_datetime(img, self.ts_now)
        if self.show_ipm:
            self.m_g2i = self.transform.calc_g2i_matrix()

            if self.show_ipm_bg:
                self.ipm = cv2.warpPerspective(img, self.m_g2i, (480, 720))
            else:
                self.ipm = np.zeros([720, 480, 3], np.uint8)
                self.ipm[:, :] = [40, 40, 40]

            self.player.show_dist_mark_ipm(self.ipm)
        ts_ana.append(('prep ipm', time.time()))

        img_aux = np.zeros([0, 427, 3], np.uint8)
        for idx, source in enumerate(self.video_cache):
            if idx > 2:
                continue
            video = self.video_cache[source]
            self.video_cache[source]['updated'] = False
            img_small = cv2.resize(cv2.imdecode(np.fromstring(video['img'], np.uint8), cv2.IMREAD_COLOR), (427, 240))
            # img_small = cv2.resize(self.jpeg_dec.decode(video['img']), (427, 240))
            video['device'] = "x1d3"
            self.player.show_video_info(img_small, video)
            img_aux = np.vstack((img_aux, img_small))
        # t1 = time.time()
        ts_ana.append(('other frame decode', time.time()))

        if 'x1_data' in mess:
            # print('------', mess['x1_data'])
            for data in mess['x1_data']:
                # print(mess['x1_data'])
                self.flow_player.draw(data, img)
        # t2 = time.time()
        ts_ana.append(('pcv_data', time.time()))
        # cache = {'rtk.2': {'type': 'rtk'}, 'rtk.3': {'type': 'rtk'}}
        misc_data = mess.get('misc')
        if misc_data:
            # print('can0 data')
            for source in list(mess['misc']):
                for entity in list(mess['misc'][source]):
                    # print(entity)
                    # try:
                    #     dt = self.ts_now - mess['misc'][source][entity]['ts']
                    # except KeyError as e:
                    #     print('error: no ts in', source, entity)
                    #     raise e
                    # if dt > 0.2 or dt < -0.2:
                    #     del mess['misc'][source][entity]
                    #     continue
                    if not self.draw_misc_data(img, mess['misc'][source][entity]):
                        print('draw misc data exited, source:', source)

        # t3 = time.time()
        ts_ana.append(('misc_data', time.time()))
        if not self.replay and self.hub.fileHandler.is_recording:
            self.player.show_recording(img, self.hub.fileHandler.start_time)

        if self.replay:
            self.player.show_replaying(img, self.ts_now - self.ts0)

        fps = self.player.cal_fps(frame_cnt)
        self.player.show_fps(img, 'video', fps)

        # if not self.replay:
        #     self.player.show_warning_ifc(img, self.supervisor.check())
        self.player.show_intrinsic_para(img)

        self.player.render_text_info(img)

        if self.show_ipm:
            # print(img.shape)
            # print(self.ipm.shape)
            padding = np.zeros((img.shape[0] - self.ipm.shape[0], self.ipm.shape[1], 3), np.uint8)

            comb = np.hstack((img, np.vstack((self.ipm, padding))))
        else:
            # comb = img
            padding = np.zeros((img.shape[0] - img_aux.shape[0], img_aux.shape[1], 3), np.uint8)
            comb = np.hstack((img, np.vstack((img_aux, padding))))

        self.frame_cost = (time.time() - t0) * 0.1 + self.frame_cost * 0.9
        self.frame_drawn_cnt += 1
        self.frame_cost_total += self.frame_cost

        # t4 = time.time()
        ts_ana.append(('others', time.time()))
        # print('pcc draw cost: video:{:.2f}ms x1_data:{:.2f}ms misc:{:.2f}ms other:{:.2f}ms total:{:.2f}ms'.format(1000*(ts_fdec-t0), 1000*(t2-t1), 1000*(t3-t2), 1000*(t4-t3), 1000*(t4-t0),))
        # print('-------------time analysis---------------')
        # for idx, ts in enumerate(ts_ana):
        #     if idx > 0:
        #         print(ts[0], '{:.2f}ms'.format(1000*(ts[1]-ts_ana[idx-1][1])))
        # print('total: {:.2f}'.format(1000*(ts_ana[-1][1]-ts_ana[0][1])))
        return comb

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
        self.player.show_drtk(img, data)
        if len(data) == 0 or data.get('source') is None:
            return

        if data['source'] == 'rtk.2':
            dt0 = data['ts'] - data['ts_origin']
            # self.rtkplot.update('rtk0', data['ts_origin'], dt0)
            self.rtk_pair[0] = data
        if 'rtk' in data['source'] and data['source'] != 'rtk.2':
            dt1 = data['ts'] - data['ts_origin']
            # self.rtkplot.update('rtk1', data['ts_origin'], dt1)
            self.rtk_pair[1] = data

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
            print('set pinpoint:', data)
            return

    def draw_rtk_ub482(self, img, data):
        self.player.show_ub482_common(img, data)
        source = data.get('source')
        # print(source)
        role = self.hub.get_veh_role(source)
        # print(role)
        # self.vehicles[role].dynamics[data['type']] = data
        self.vehicles[role].update_dynamics(data)

        if data['type'] == 'pinpoint':
            self.update_pinpoint(data)

        if role in ('ego', 'default'):
            host = self.vehicles['ego'].get_pos()
            if 'lat' in data:
                if self.set_pinpoint:
                    self.set_pinpoint = False
                    pp = data.copy()
                    pp['type'] = 'pinpoint'
                    self.update_pinpoint(pp)
                    # self.vehicles['ego'].dynamics['pinpoint'] = data
                    # self.hub.fileHandler.insert_raw(
                    #     (data['ts'], source + '.pinpoint', compose_from_def(ub482_defs, data)))
                    # print('set pinpoint:', data)
                if self.gga is None and self.en_gga and not self.replay:
                    server = self.cfg.runtime['modules']['GGA_reporter']['ntrip_address']
                    port = self.cfg.runtime['modules']['GGA_reporter']['port']
                    self.gga = GGAReporter(server, port)
                    self.gga.start()
                if self.gga is not None and not self.replay:
                    self.gga.set_pos(data['lat'], data['lon']) if data['pos_type'] != 'NONE' else None
                    if data['pos_type'] != 'NONE':
                        self.statistics['GGA_report_coord'] = 'Lat:{lat:.8f}  Lon:{lon:.8f}  Hgt:{hgt:.3f}'.format(**data)
            elif 'yaw' in data:
                self.player.show_heading_horizen(img, data)
        else:  # other vehicle
            # print('other role:', role)
            if self.vehicles['ego']:
                target = get_rover_target(self.vehicles['ego'], self.vehicles[role])
                # print(target)
                if target:
                    self.player.show_rtk_target(img, target)
                    self.player.show_rtk_target_ipm(self.ipm, target)
            # else:
            #     print('no ego vehicle')
            # elif 'trk_gnd' in data:
            #     self.player.show_track_gnd(img, data)
            # ppq = self.vehicles['ego'].dynamics.get('pinpoint')
            # pp = {'source': 'rtk.3', 'lat': 22.546303, 'lon': 113.942000, 'hgt': 35.0}
            # if ppq and host and data['ts'] - host['ts'] < 0.1:
            #     pp1 = ppq[0]
            #     self.player.show_target(img, pp1, host)

        pp_target = self.vehicles['ego'].get_pp_target()
        if pp_target:
            # t0 = time.time()
            self.player.show_rtk_target(img, pp_target)
            self.player.show_rtk_target_ipm(self.ipm, pp_target)
            # dt = time.time() - t0
            # print('rtk target cost:{}'.format(dt * 1000))
            # print(pp_target['ts'])

        # else:  # other vehicle
        #     host = self.vehicles['ego'].get_pos()
        # if 'lat' in data and host:
        #     self.player.show_target(img, data, host)
        # pass

        # if 'lat' in data and not self.replay:
        #     if self.gga is None and self.en_gga:
        #         self.gga = GGAReporter('ntrip.weaty.cn', 5001)
        #         self.gga.start()
        #     if self.gga is not None:
        #         self.gga.set_pos(data['lat'], data['lon']) if data['pos_type'] != 'NONE' else None
        #     # print('role:', self.hub.get_veh_role(data['source']))
        #     if self.hub.get_veh_role(data['source']) == 'ego':
        #         self.vehicles['ego'].dynamics['rtkpos'] = data
        #         if self.set_pinpoint:
        #             self.set_pinpoint = False
        #             self.vehicles['ego'].dynamics['pinpoint'] = data
        #             self.hub.fileHandler.insert_raw(
        #                 (data['ts'], data['source'] + '.pinpoint', compose_from_def(ub482_defs, data)))
        #             print('set pinpoint:', data)
        #         pp = self.vehicles['ego'].dynamics.get('pinpoint')
        #         if pp:
        #             self.player.show_target(img, pp, data)
        #     else:  # not ego car
        #         self.player.show_target(img, data, self.vehicles['ego'].dynamics.get('rtkpos'))
        #
        # if data['source'] == 'rtk.5':
        #     if 'lat' in data:
        #         self.rtk_pair[0] = data
        #         # if not self.replay:
        #         #     self.gga.set_pos(data['lat'], data['lon'])
        #     if 'yaw' in data:
        #         self.rtk_pair[0]['yaw'] = data['yaw']
        # if 'rtk' in data['source'] and data['source'] != 'rtk.5':
        #     if 'lat' in data:
        #         self.rtk_pair[1] = data
        #     if 'yaw' in data:
        #         self.rtk_pair[1]['yaw'] = data['yaw']
        #
        # if 'lat' in self.rtk_pair[0] and 'lat' in self.rtk_pair[1] and 'yaw' in self.rtk_pair[0] and 'yaw' in \
        #         self.rtk_pair[1]:
        #     self.player.show_target(img, self.rtk_pair[1], self.rtk_pair[0])
        #     if self.show_ipm:
        #         self.player.show_ipm_target(self.ipm, self.rtk_pair[1], self.rtk_pair[0])

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

    def draw_misc_data(self, img, data):
        # print(data)
        if 'type' not in data:
            print('data invalid: no type', data)
            return
        role = self.hub.get_veh_role(data.get('source'))
        if role not in self.vehicles:
            self.vehicles[role] = Vehicle(role)

        if data['type'] == 'pcv_data':
            # print('pcv_data', data)
            self.flow_player.draw(data, img)

        elif data['type'] == 'obstacle':
            # dummy0 = {'type': 'obstacle', 'id': 20, 'source': 'x1.1', 'pos_lat': 0, 'pos_lon': 60, 'color': 1}
            # dummy1 = {'type': 'obstacle', 'id': 20, 'source': 'esr.0', 'sensor': 'radar', 'pos_lat': 0, 'pos_lon': 60, 'color': 2}
            # self.player.show_obs(img, dummy0)
            # self.player.show_obs(img, dummy1)

            self.player.show_obs(img, data)
            self.player.update_column_ts(data.get('source'), data.get('ts'))
            if self.show_ipm:
                # self.player.show_ipm_obs(self.ipm, dummy0)
                # self.player.show_ipm_obs(self.ipm, dummy1)
                self.player.show_ipm_obs(self.ipm, data)
            if data.get('cipo'):
                self.cipv = data
        # lane
        elif data['type'] == 'lane':
            self.player.draw_lane_r(img, data, )
            if self.show_ipm:
                self.player.draw_lane_ipm(self.ipm, data)
        # vehicle
        elif data['type'] == 'vehicle_state':
            self.player.draw_vehicle_state(img, data)
            # print(data)
            self.player.update_column_ts(data['source'], data['ts'])
            if 'yaw_rate' in data and not self.cfg.runtime.get('low_profile'):
                # self.player.show_host_path(img, data['speed'], data['yaw_rate'], self.cipv)
                self.player.show_host_path_ipm(self.ipm, data['speed'], data['yaw_rate'])

        elif data['type'] == 'CIPV':
            self.cipv = data

        elif data['type'] == 'rtk':
            # print('------------', data['type'])
            data['updated'] = True
            self.draw_rtk(img, data)

        elif data['type'] in ['bestpos', 'heading', 'bestvel', 'pinpoint']:
            # print('------------', data['type'])
            self.draw_rtk_ub482(img, data)
            self.player.update_column_ts(data['source'], data['ts'])
        elif data['type'] == 'rtcm':
            self.viz_rtcm(img, data)
        elif data['type'] == 'gps':
            self.player.show_gps(data)
            self.player.update_column_ts(data['source'], data['ts'])
        elif data['type'] == 'traffic_sign':
            # print(data)
            self.player.show_tsr(img, data)
            # self.pause = True
        elif data['type'] == 'warning':
            self.player.show_warning(img, data)
        elif data['type'] == 'profiling':
            self.analyze_profile(img, data)
        self.specific_handle(img, data)
        return True

    def handle_keyboard(self):
        key = cv2.waitKey(1) & 0xFF
        self.control(key)

    def control(self, key):
        if key == ord('q') or key == 27:
            if not self.to_web:
                cv2.destroyAllWindows()
            # os._exit(0)
            self.exit = True
            # sys.exit(0)
        elif key == 32:  # space
            self.pause = not self.pause
            print('Pause:', self.pause)
            if self.pause:
                self.pause_t = time.time()
            else:
                paused_t = time.time() - self.pause_t
                self.hub.add_pause(paused_t)

        elif key == ord('r'):
            if self.hub.fileHandler.is_recording:
                # self.recording = False
                self.stop_rec()
                # self.parse_state = True
                self.hub.parse_can_msgs(self.parse_state)

            else:
                # self.recording = True
                self.start_rec()
                # self.parse_state = False
                if self.cfg.runtime.get('low_profile'):
                    self.hub.parse_can_msgs(False)
            print('toggle recording status. {}'.format(self.hub.fileHandler.is_recording))
        elif key == ord('s'):
            self.ot.save_para()
            if not self.replay:
                self.hub.fileHandler.save_param()
        elif key == ord('p'):
            self.set_pinpoint = True
            # print(self.set_target)
        elif key == ord('c'):
            self.calib_esr()
        elif key == ord('b'):
            self.show_ipm_bg = not self.show_ipm_bg
        elif key == ord('i'):
            self.sv_state = next(self.sideview_state)
            self.show_ipm = not self.show_ipm
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
            print('save PP.')
            self.hub.fileHandler.insert_raw(
                (pp['ts'], pp.get('source') + '.pinpoint', compose_from_def(ub482_defs, pp)))

    def stop_rec(self):
        self.hub.fileHandler.stop_rec()

    def left_click(self, event, x, y, flags, param):
        # print(event, x, y, flags, param)
        if cv2.EVENT_LBUTTONDOWN == event:
            print('left btn down', x, y)

    def check_status(self):
        if self.hub.msg_queue.full():
            self.stuck_cnt += 1
        else:
            self.stuck_cnt = 0
        if not self.hub.time_aligned:
            return {'status': 'fail', 'info': 'collectors\' time not aligned!'}
        return {'status': 'ok', 'info': 'oj8k'}

    def send_online_devices(self):
        if not self.to_web:
            return
        msg = self.hub.online
        # self.vs.ws_send('devices', msg)
        if self.o_msg_q and not self.o_msg_q.full():
            self.o_msg_q.put(('devices', msg))
        # print('sent online devices')
        return {'status': 'ok', 'info': 'oj8k'}

    def send_statistics(self):
        if not self.to_web:
            return

        self.statistics['cpu_mem_info'] = 'cpu_used: {}% mem_used {}% cpu_temp: {}c'.format(get_cpu_pct(), get_mem_pct(), get_cpu_temp())

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
            data = '{} {} {} {} {}'.format(self.now_id, d_azu, azu_rtk, azu_esr, dt)
            log_line = "%.10d %.6d " % (tv_s, tv_us) + 'esr.calib' + ' ' + data + "\n"
            cf.write(log_line)


class HeadlessPCC:
    def __init__(self, hub):
        self.hub = hub
        self.hub.fileHandler.isheadless = True

    def start(self):
        # self.hub.start()
        while True:
            mess = self.hub.pop_simple()

            if mess is None or not mess.get('frame_id'):
                continue
            frame_id = mess['frame_id']
            # if self.cfg.local_cfg.save.video:
            self.hub.fileHandler.insert_video(
                {'ts': mess['ts'], 'frame_id': frame_id, 'img': mess['img'], 'source': 'video'})
            time.sleep(0.02)


if __name__ == "__main__":
    import sys

    local_path = os.path.split(os.path.realpath(__file__))[0]
    # print('local_path:', local_path)
    os.chdir(local_path)

    if len(sys.argv) == 1:
        sys.argv.append('config/cfg_lab.json')

    if '--direct' in sys.argv:
        print('direct mode.')
        hub = Hub(direct_cfg=sys.argv[2])
        pcc = PCC(hub, ipm=True, replay=False)
        pcc.start()

    elif '--headless' in sys.argv:
        print('headless mode.')
        hub = Hub(headless=True)
        hub.start()
        pcc = HeadlessPCC(hub)

        t = Thread(target=pcc.start)
        t.start()
        # hub.fileHandler.start_rec()
        # pcc.start()

        from tornado.web import Application, RequestHandler, StaticFileHandler
        from tornado.ioloop import IOLoop


        class IndexHandler(RequestHandler):
            def post(self):
                action = self.get_body_argument('action')
                if action:
                    if 'start' in action:
                        if not hub.fileHandler.recording:
                            hub.fileHandler.start_rec()
                            print(hub.fileHandler.recording)
                            self.write({'status': 'ok', 'action': action, 'message': 'start recording'})
                        else:
                            self.write({'status': 'ok', 'message': 'already recording', 'action': action})
                    elif 'stop' in action:
                        if not hub.fileHandler.recording:
                            self.write({'status': 'ok', 'message': 'not recording', 'action': action})
                        else:
                            hub.fileHandler.stop_rec()
                            print(hub.fileHandler.recording)
                            self.write({'status': 'ok', 'action': action, 'message': 'stop recording'})
                    elif 'check' in action:
                        mess = 'recording' if hub.fileHandler.recording else 'not recording'
                        self.write({'status': 'ok', 'action': action, 'message': mess})
                    elif 'image' in action:
                        img = hub.fileHandler.get_last_image()
                        img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
                        if img is None:
                            # print('pcc', img)
                            # img = cv2.imdecode(np.fromstring(img, np.uint8), cv2.IMREAD_COLOR)
                            img = cv2.imread("./web/statics/jpg/160158-1541059318e139.jpg", cv2.IMREAD_COLOR)

                        base64_str = cv2.imencode('.jpg', img)[1].tostring()
                        base64_str = base64.b64encode(base64_str).decode()
                        self.write({'status': 'ok', 'action': action, 'message': 'get image', 'data': base64_str})
                    else:
                        self.write({'status': 'ok', 'message': 'unrecognized action', 'action': action})
                else:
                    # self.hub.fileHandler.stop_rec()
                    self.write({'status': 'error', 'message': 'not action', 'action': None})

            def get(self):
                self.render("web/index.html")


        app = Application([
            (r'/', IndexHandler),
            (r"/static/(.*)", StaticFileHandler, {"path": "web/statics"}),
        ], debug=False)
        app.listen(9999)
        IOLoop.instance().start()

    else:
        print('normal mode.')
        uni_conf = load_cfg(sys.argv[1])
        hub = Hub()
        pcc = PCC(hub, ipm=False, replay=False)
        pcc.start()

    # pcc = PCC(hub, ipm=True, replay=False)
    # pcc.start()
