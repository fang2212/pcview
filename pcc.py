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

import cv2
import numpy as np

from config.config import local_cfg, load_cfg
from net.ntrip_client import GGAReporter
from player import FlowPlayer
from player.pcc_ui import Player
from recorder import VideoRecorder
from recorder.convert import *
from sink.hub import Hub
from tools.geo import *
from tools.match import is_near
from tools.mytools import Supervisor
from tools.transform import Transform, OrientTuner
from tools.vehicle import Vehicle

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def loop_traverse(items):
    while True:
        for item in items:
            yield item


class PCC(object):

    def __init__(self, hub, replay=False, rlog=None, ipm=None, save_replay_video=None, uniconf=None):
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
        self.pre_rtk = {}
        self.ts_now = 0
        self.cipv = 0
        self.msg_cnt = {}
        self.transform = Transform(uniconf)
        self.m_g2i = self.transform.calc_g2i_matrix()
        self.ipm = None
        self.show_ipm = ipm
        self.set_pinpoint = False
        self.target = None
        self.rtk_pair = [{}, {}]
        self.ot = OrientTuner(uniconf)
        self.show_ipm_bg = False

        # self.ego_car = Vehicle()
        self.vehicles = {'ego': Vehicle('ego')}
        self.calib_data = dict()
        self.frame_cost = 0
        self.video_cache = {}
        cv2.namedWindow('MINIEYE-CVE')
        cv2.namedWindow('adj')
        # cv2.resizeWindow('adj', 600, 600)
        self.sideview_state = loop_traverse(['ipm', 'video_aux'])
        self.sv_state = 'ipm'
        # self.rt_param = self.cfg.runtime
        # cv2.namedWindow('video_aux')
        cv2.createTrackbar('Yaw  ', 'adj', 500, 1000, self.ot.update_yaw)
        cv2.createTrackbar('Pitch', 'adj', 500, 1000, self.ot.update_pitch)
        cv2.createTrackbar('Roll  ', 'adj', 500, 1000, self.ot.update_roll)
        cv2.createTrackbar('ESR_y', 'adj', 500, 1000, self.ot.update_esr_yaw)
        if not replay:
            self.supervisor = Supervisor([self.check_status,
                                          self.hub.fileHandler.check_file])
            self.supervisor.start()
            # self.gga = GGAReporter('ntrip.weaty.cn', 5001)
            # self.gga.start()
        else:
            self.hub.d = Manager().dict()

            def update_speed(x):
                self.hub.d['replay_speed'] = 1 if x // 10 < 1 else x // 10
                print('replay-speed is', self.hub.d['replay_speed'])

            cv2.createTrackbar('replay-speed', 'adj', 10, 50, update_speed)

        cv2.setMouseCallback('MINIEYE-CVE', self.left_click, '1234')
        self.gga = None
        if not self.replay:
            self.en_gga = self.cfg.runtime['modules']['GGA_reporter']['enable']
        else:
            self.en_gga = False
        self.flow_player = FlowPlayer()

        self.save_replay_video = save_replay_video

        if self.save_replay_video and self.replay:
            self.vw = VideoRecorder(os.path.dirname(self.rlog), fps=20)
            self.vw.set_writer("replay-render", 1760, 720)
            print('--------save replay video', os.path.dirname(self.rlog))

    def start(self):
        self.hub.start()
        self.player.start_time = datetime.now()
        frame_cnt = 0
        data_cnt = 0

        while not self.exit:
            d = self.hub.pop_simple()
            if d is None or not d.get('frame_id'):
                # time.sleep(0.01)
                continue
            if not self.replay:
                qsize = self.hub.fileHandler.raw_queue.qsize()
                # print(qsize)
                if self.hub.fileHandler.recording and qsize > 2000:
                    print('msg_q critical, skip drawing.', qsize)
                    time.sleep(0.1)
                    continue
            self.draw(d, frame_cnt)
            while self.replay and self.pause:
                self.draw(d, frame_cnt)
                self.hub.pause(True)
                time.sleep(0.1)
            if self.replay:
                self.hub.pause(False)
                if self.hub.d:
                    frame_cnt += self.hub.d['replay_speed'] - 1
                    # print(frame_cnt)
            # self.draw(d, frame_cnt)
            frame_cnt += 1
            if frame_cnt > 500:
                self.player.start_time = datetime.now()
                frame_cnt = 1
            # time.sleep(0.01)

    def draw(self, mess, frame_cnt):
        # print(mess[''])
        t0 = time.time()
        try:
            imgraw = cv2.imdecode(np.fromstring(mess['img'], np.uint8), cv2.IMREAD_COLOR)
            img = imgraw.copy()
        except Exception as e:
            print(e)
            return

        frame_id = mess['frame_id']
        self.now_id = frame_id
        self.ts_now = mess['ts']
        self.player.ts_now = mess['ts']
        self.player.update_column_ts('video', mess['ts'])
        # print(mess)
        can_data = mess.get('can')
        if self.ts0 == 0:
            self.ts0 = self.ts_now

        if local_cfg.save.video and not self.replay:
            self.hub.fileHandler.insert_video(
                {'ts': mess['ts'], 'frame_id': frame_id, 'img': imgraw, 'source': 'video'})

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

        img_aux = np.zeros([0, 427, 3], np.uint8)
        if 'video_aux' in mess:
            # print(mess['video_aux'])
            for video in mess['video_aux']:
                if len(video) > 0:
                    self.video_cache[video['source']] = video
                    self.video_cache[video['source']]['updated'] = True

        for idx, source in enumerate(self.video_cache):
            if idx > 2:
                continue
            video = self.video_cache[source]
            # print('incoming video', video['source'])
            img_raw = cv2.imdecode(np.fromstring(video['img'], np.uint8), cv2.IMREAD_COLOR)
            if self.video_cache[source]['updated']:
                self.hub.fileHandler.insert_video(
                    {'ts': video['ts'], 'frame_id': video['frame_id'], 'img': img_raw, 'source': video['source']})
            self.video_cache[source]['updated'] = False
            img_small = cv2.resize(img_raw, (427, 240))
            self.player.show_video_info(img_small, video)
            img_aux = np.vstack((img_aux, img_small))

        if 'x1_data' in mess:
            # print('------', mess['pcv_data'])
            for data in mess['x1_data']:
                # print(mess['x1_data'])
                self.flow_player.draw(data, img)

        # cache = {'rtk.2': {'type': 'rtk'}, 'rtk.3': {'type': 'rtk'}}
        if can_data:
            # print('can0 data')
            for d in mess['can']:
                if not d:
                    continue
                self.draw_can_data(img, d)
                # if 'type' in d:
                #     if d['type'] == 'rtk':
                #         cache[d['source']] = d
                #     else:
                #         self.draw_can_data(img, d)
                # else:
                #     tt = 1

        # for type in cache:
        #     d = cache[type]
        #     self.draw_can_data(img, d)

        if 'rtk' in mess and mess['rtk']:  # usb pcan rtk
            for d in mess['rtk']:
                # print('----------- rtk')
                self.draw_rtk(img, d)
                if self.set_pinpoint:
                    self.set_pinpoint = False
                    self.target = {'lat': d['lat'], 'lon': d['lon'], 'hgt': d['hgt'], 'rtkst': d['rtkst']}
                    self.hub.fileHandler.insert_raw((d['ts'], 'rtkpin', '{} {} {} {}'.format(
                        d['rtkst'], d['lat'], d['lon'], d['hgt'])))
                    print('set pinpoint:', d)

        if not self.replay and self.hub.fileHandler.recording:
            self.player.show_recording(img, self.hub.fileHandler.start_time)

        if self.replay:
            self.player.show_replaying(img, self.ts_now - self.ts0)

        fps = self.player.cal_fps(frame_cnt)
        self.player.show_fps(img, 'video', fps)

        if not self.replay:
            self.player.show_warning(img, self.supervisor.check())
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

        cv2.imshow('MINIEYE-CVE', comb)

        if self.save_replay_video and self.replay:
            self.vw.write(comb)
            # print(comb.shape)

        self.handle_keyboard()
        self.frame_cost = (time.time() - t0) * 0.1 + self.frame_cost * 0.9

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
        role = self.hub.get_veh_role(source)
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
            elif 'yaw' in data:
                self.player.show_heading_horizen(img, data)
            elif 'trk_gnd' in data:
                self.player.show_track_gnd(img, data)
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

        else:  # other vehicle
            host = self.vehicles['ego'].get_pos()
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

    def draw_can_data(self, img, data):
        # print(data)
        role = self.hub.get_veh_role(data.get('source'))
        if role not in self.vehicles:
            self.vehicles[role] = Vehicle(role)

        if data['type'] == 'obstacle':
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

        elif data['type'] == 'CIPV':
            self.cipv = data['id']

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
        self.specific_handle(img, data)

    def handle_keyboard(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            # os._exit(0)
            self.exit = True
            sys.exit(0)
        elif key == 32:  # space
            self.pause = not self.pause
            print('Pause:', self.pause)

        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True
        elif key == ord('r'):
            if self.hub.fileHandler.recording:
                # self.recording = False
                self.hub.fileHandler.stop_rec()
            else:
                # self.recording = True
                self.hub.fileHandler.start_rec(self.rlog)
            print('toggle recording status. {}'.format(self.hub.fileHandler.recording))
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

    def left_click(self, event, x, y, flags, param):
        # print(event, x, y, flags, param)
        if cv2.EVENT_LBUTTONDOWN == event:
            print('left btn down', x, y)

    def check_status(self):
        if not self.hub.time_aligned:
            return {'status': 'fail', 'info': 'collectors\' time not aligned!'}
        return {'status': 'ok', 'info': 'oj8k'}

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
            if local_cfg.save.video:
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
