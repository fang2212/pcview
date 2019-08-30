#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from math import fabs
import logging
from multiprocessing import Manager
import cv2
from datetime import datetime
from tools.mytools import Supervisor, OrientTuner
from tools.transform import Transform
from config.config import local_cfg
from player.pcc_ui import Player
from sink.hub import Hub
from tools.vehicle import Vehicle
from tools.match import is_near
import numpy as np


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class PCC(object):
    def __init__(self, hub, replay=False, rlog=None, ipm=None):
        self.hub = hub
        self.player = Player()
        self.exit = False
        self.pause = False
        # self.recording = False
        self.replay = replay
        self.rlog = rlog
        self.frame_idx = 0

        self.now_id = 0
        self.pre_rtk = {}
        self.ts_now = 0
        self.cipv = 0
        self.msg_cnt = {}
        self.transform = Transform()
        self.m_g2i = self.transform.calc_g2i_matrix()
        self.ipm = None
        self.show_ipm = ipm
        self.set_target = False
        self.target = None
        self.rtk_pair = [{}, {}]
        self.ot = OrientTuner()
        self.show_ipm_bg = False

        self.ego_car = Vehicle()
        self.calib_data = dict()
        cv2.namedWindow('UI')
        cv2.createTrackbar('Yaw', 'UI', 500, 1000, self.ot.update_yaw)
        cv2.createTrackbar('Pitch', 'UI', 500, 1000, self.ot.update_pitch)
        cv2.createTrackbar('Roll', 'UI', 500, 1000, self.ot.update_roll)
        cv2.createTrackbar('ESR_Yaw', 'UI', 500, 1000, self.ot.update_esr_yaw)
        if not replay:
            self.supervisor = Supervisor([self.check_status, self.hub.fileHandler.check_file])
            self.supervisor.start()
        else:
            self.hub.d = Manager().dict()
            def update_speed(x):
                self.hub.d['replay_speed'] = 1 if x//10 < 1 else x//10
                print('replay-speed is', self.hub.d['replay_speed'])
            cv2.createTrackbar('replay-speed', 'UI', 10, 50, update_speed)

        cv2.setMouseCallback('UI', self.left_click, '1234')

    def start(self):
        self.hub.start()
        self.player.start_time = datetime.now()
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop_simple()
            if d is None or not d.get('frame_id'):
                continue
            self.draw(d, frame_cnt)
            while self.replay and self.pause:
                self.draw(d, frame_cnt)
                self.hub.pause(True)
            if self.replay:
                self.hub.pause(False)
                if self.hub.d:
                    frame_cnt += self.hub.d['replay_speed'] - 1
                    # print(frame_cnt)
            # self.draw(d, frame_cnt)
            frame_cnt += 1

    def draw(self, mess, frame_cnt):
        imgraw = cv2.imdecode(np.fromstring(mess['img'], np.uint8), cv2.IMREAD_COLOR)
        img = imgraw.copy()
        frame_id = mess['frame_id']
        self.now_id = frame_id
        self.ts_now = mess['ts']
        # print(mess)
        can_data = mess.get('can')

        self.player.show_columns(img)

        self.player.show_frame_id(img, frame_id)
        self.player.show_datetime(img, self.ts_now)
        if self.show_ipm:
            self.m_g2i = self.transform.calc_g2i_matrix()

            if self.show_ipm_bg:
                self.ipm = cv2.warpPerspective(img, self.m_g2i, (480, 720))
            else:
                self.ipm = np.zeros([720, 480, 3], np.uint8)
                self.ipm[:, :] = [180, 180, 180]

            self.player.show_dist_mark_ipm(self.ipm)

        cache = {'rtk.2': {'type': 'rtk'}, 'rtk.3': {'type': 'rtk'}}
        if can_data:
            # print('can0 data')
            for d in mess['can']:
                if not d:
                    continue
                if d['type'] == 'rtk':
                    cache[d['source']] = d
                else:
                    self.draw_can_data(img, d)

        for type in cache:
            d = cache[type]
            self.draw_can_data(img, d)

        if 'rtk' in mess and mess['rtk']:  # usb pcan rtk
            for d in mess['rtk']:
                # print('----------- rtk')
                self.draw_rtk(img, d)
                if self.set_target:
                    self.target = {'lat': d['lat'], 'lon': d['lon'], 'hgt': d['hgt'], 'rtkst': d['rtkst']}
                    self.hub.fileHandler.insert_raw((d['ts'], 'rtkpin', '{} {} {} {}'.format(
                        d['rtkst'], d['lat'], d['lon'], d['hgt'])))
                    self.set_target = False

        if not self.replay and self.hub.fileHandler.recording:
            self.player.show_recording(img, self.hub.fileHandler.start_time)

        fps = self.player.cal_fps(frame_cnt)
        self.player.show_fps(img, fps)

        if not self.replay:
            self.player.show_warning(img, self.supervisor.check())
        self.player.show_intrinsic_para(img)

        if self.show_ipm:
            comb = np.hstack((img, self.ipm))
        else:
            comb = img
        cv2.imshow('UI', comb)

        self.handle_keyboard()

    def draw_rtk(self, img, data):
        self.player.show_rtk(img, data)
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

    def draw_rtk_ub482(self, img, data):
        self.player.show_ub482_common(img, data)
        if data['source'] == 'rtk.5':
            if 'lat' in data:
                self.rtk_pair[0] = data
            if 'yaw' in data:
                self.rtk_pair[0]['yaw'] = data['yaw']
        if 'rtk' in data['source'] and data['source'] != 'rtk.5':
            if 'lat' in data:
                self.rtk_pair[1] = data
            if 'yaw' in data:
                self.rtk_pair[1]['yaw'] = data['yaw']

        if 'lat' in self.rtk_pair[0] and 'lat' in self.rtk_pair[1] and 'yaw' in self.rtk_pair[0] and 'yaw' in \
                self.rtk_pair[1]:
            self.player.show_target(img, self.rtk_pair[1], self.rtk_pair[0])
            if self.show_ipm:
                self.player.show_ipm_target(self.ipm, self.rtk_pair[1], self.rtk_pair[0])

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
        if data['type'] == 'obstacle':
            # dummy0 = {'type': 'obstacle', 'id': 20, 'source': 'x1.1', 'pos_lat': 0, 'pos_lon': 60, 'color': 1}
            # dummy1 = {'type': 'obstacle', 'id': 20, 'source': 'esr.0', 'sensor': 'radar', 'pos_lat': 0, 'pos_lon': 60, 'color': 2}
            # self.player.show_obs(img, dummy0)
            # self.player.show_obs(img, dummy1)
            self.player.show_obs(img, data)
            if self.show_ipm:
                # self.player.show_ipm_obs(self.ipm, dummy0)
                # self.player.show_ipm_obs(self.ipm, dummy1)
                self.player.show_ipm_obs(self.ipm, data)

        elif data['type'] == 'lane':
            self.player.draw_lane_r(img, data)
            if self.show_ipm:
                self.player.show_lane_ipm(self.ipm, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'])

        elif data['type'] == 'vehicle_state':
            self.player.draw_vehicle_state(img, data)
        elif data['type'] == 'CIPV':
            self.cipv = data['id']
        elif data['type'] == 'rtk':
            # print('------------', data['type'])
            data['updated'] = True
            self.draw_rtk(img, data)
        elif data['type'] == 'bestpos':
            # print('------------', data['type'])
            self.draw_rtk_ub482(img, data)
        elif data['type'] == 'heading':
            # print('------------', data['type'])
            self.draw_rtk_ub482(img, data)
        elif data['type'] == 'rtcm':
            # print('------------', data['type'])
            self.draw_rtk_ub482(img, data)

        self.specific_handle(img, data)

    def handle_keyboard(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            # os._exit(0)
            self.exit = True
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
        elif key == ord('d'):
            self.set_target = True
            # print(self.set_target)
        elif key == ord('c'):
            self.calib_esr()
        elif key == ord('b'):
            self.show_ipm_bg = not self.show_ipm_bg

    def left_click(self, event, x, y, flags, param):
        # print(event, x, y, flags, param)
        if cv2.EVENT_LBUTTONDOWN == event:
            print('left btn down', x, y)

    def check_status(self):
        if not self.hub.time_aligned:
            return {'status': 'fail', 'info': 'collectorss\' time not aligned!'}
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


if __name__ == "__main__":
    import sys
    from config.config import load_cfg
    load_cfg('config/cfg_superb.json')

    hub = Hub()
    if len(sys.argv) == 2 and '--headless' in sys.argv[1]:
        hub.start()
        import json
        from tornado.web import Application, RequestHandler
        from tornado.ioloop import IOLoop
        class IndexHandler(RequestHandler):
            def post(self):
                action = self.get_body_argument('action')
                if action:
                    if 'start' in action:
                        if not hub.fileHandler.recording:
                            hub.fileHandler.start_rec()
                            print(hub.fileHandler.recording)
                            self.write(json.dumps({'status': 'ok', 'action': action, 'message': 'start recording'}))
                        else:
                            self.write(json.dumps({'status': 'ok', 'message': 'already recording', 'action': action}))
                    elif 'stop' in action:
                        if not hub.fileHandler.recording:
                            self.write(json.dumps({'status': 'ok', 'message': 'not recording', 'action': action}))
                        else:
                            hub.fileHandler.stop_rec()
                            print(hub.fileHandler.recording)
                            self.write(json.dumps({'status': 'ok', 'action': action, 'message': 'stop recording'}))
                    elif 'check' in action:
                        mess = 'recording' if hub.fileHandler.recording else 'not recording'
                        self.write(json.dumps({'status': 'ok', 'action': action, 'message': mess}))
                    else:
                        self.write(json.dumps({'status': 'ok', 'message': 'unrecognized action', 'action': action}))
                else:
                    # self.hub.fileHandler.stop_rec()
                    self.write(json.dumps({'status': 'error', 'message': 'not action', 'action': None}))
        app = Application([(r'/', IndexHandler)])
        app.listen(9999)
        IOLoop.instance().start()

    else:
        pcc = PCC(hub, ipm=True, replay=False)
        pcc.start()

    # pcc = PCC(hub, ipm=True, replay=False)
    # pcc.start()
