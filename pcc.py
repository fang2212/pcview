#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from config.config import local_cfg, install
import cv2
from tools.transform import calc_g2i_matrix, update_m_r2i
from datetime import datetime
from player.pcc_ui import Player
from sink.hub import Hub
from multiprocessing.dummy import Process as Thread
import time
from tools.vehicle import Vehicle
import numpy as np
from tools.match import is_near
from math import fabs
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class OrientTuner(object):
    def __init__(self, y=install['video']['yaw'], p=install['video']['pitch'], r=install['video']['roll'],  ey=install['esr']['yaw']):
        self.yaw = y
        self.pitch = p
        self.roll = r
        self.esr_yaw = ey

    def update_yaw(self, x):
        self.yaw = install['video']['yaw'] - 0.01 * (x - 500)
        # self.pitch = install['video']['pitch']
        # self.roll = install['video']['roll']

        update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_pitch(self, x):
        # self.yaw = install['video']['yaw']
        self.pitch = install['video']['pitch'] - 0.01 * (x - 500)
        # self.roll = install['video']['roll']

        update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_roll(self, x):
        # self.yaw = install['video']['yaw']
        self.roll = install['video']['roll'] - 0.01 * (x - 500)
        # self.roll = install['video']['roll']

        update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_esr_yaw(self, x):
        self.esr_yaw = install['esr']['yaw'] - 0.01 * (x - 500)
        # self.pitch = install['video']['pitch']
        # self.roll = install['video']['roll']

        update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def save_para(self):
        install['video']['yaw'] = self.yaw
        install['video']['pitch'] = self.pitch
        install['video']['roll'] = self.roll


class Supervisor(Thread):
    def __init__(self, checkers=[]):
        super(Supervisor, self).__init__()
        self.checkers = checkers
        self.result = []

    def run(self):
        while True:
            self.result.clear()
            for checker in self.checkers:
                ret = checker()
                if ret.get('status') is not 'ok':
                    self.result.append(ret.get('info'))
            time.sleep(1)

    def check(self):
        return self.result


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
        self.m_g2i = calc_g2i_matrix()
        self.ipm = None
        self.show_ipm = ipm
        self.set_target = False
        self.target = None
        self.rtk_pair = [{}, {}]
        self.ot = OrientTuner()
        self.show_ipm_bg = False

        if not replay:
            self.supervisor = Supervisor([self.check_status, self.hub.fileHandler.check_file])
            self.supervisor.start()
        self.ego_car = Vehicle()
        self.calib_data = dict()
        cv2.namedWindow('UI')
        cv2.createTrackbar('Yaw', 'UI', 500, 1000, self.ot.update_yaw)
        cv2.createTrackbar('Pitch', 'UI', 500, 1000, self.ot.update_pitch)
        cv2.createTrackbar('Roll', 'UI', 500, 1000, self.ot.update_roll)
        cv2.createTrackbar('ESR_Yaw', 'UI', 500, 1000, self.ot.update_esr_yaw)
        cv2.setMouseCallback('UI', self.left_click, '1234')

    def start(self):
        self.hub.start()
        self.player.start_time = datetime.now()
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop_simple()
            if d is None or not d.get('frame_id'):
                # time.sleep(0.001)
                continue

            self.draw(d, frame_cnt)
            time.sleep(0.01)
            while self.replay and self.pause:
                self.draw(d, frame_cnt)
                self.hub.pause(True)
                time.sleep(0.05)
            # cv2.waitKey(1)
            self.hub.pause(False)
            # self.draw(d, frame_cnt)
            if frame_cnt >= 200:
                self.player.start_time = datetime.now()
                frame_cnt = 0
                time.sleep(0.01)

    def draw(self, mess, frame_cnt):
        imgraw = cv2.imdecode(np.fromstring(mess['img'], np.uint8), cv2.IMREAD_COLOR)
        img = imgraw.copy()
        frame_id = mess['frame_id']
        self.now_id = frame_id
        self.ts_now = mess['ts']
        # print(mess)
        can_data = mess.get('can')

        if local_cfg.save.video and not self.replay:
            self.hub.fileHandler.insert_video((mess['ts'], frame_id, imgraw))

        self.player.show_columns(img)

        self.player.show_frame_id(img, frame_id)
        self.player.show_datetime(img, self.ts_now)
        if self.show_ipm:
            self.m_g2i = calc_g2i_matrix()

            if self.show_ipm_bg:
                self.ipm = cv2.warpPerspective(img, self.m_g2i, (480, 720))
            else:
                self.ipm = np.zeros([720, 480, 3], np.uint8)
                self.ipm[:, :] = [180, 180, 180]

            self.player.show_dist_mark_ipm(self.ipm)

        cache = {'rtk.2': {'type': 'rtk'}, 'rtk.3': {'type': 'rtk'}}

        print('-----------mess', mess['can'])
        if can_data:
            # print('can0 data')
            for d in mess['can']:
                if not d:
                    continue
                if d['type'] == 'rtk':
                    cache[d['source']] = d
                else:
                    self.draw_can_data(img, d)
                print('----------d', d)

        for type in cache:
            d = cache[type]
            self.draw_can_data(img, d)


        if 'rtk' in mess and mess['rtk']:  # usb pcan rtk
            for d in mess['rtk']:
                # print('rtk')
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
        # draw_corners(img)
        # cv2.imshow('UI', img)
        # cv2.imshow('IPM', self.ipm)
        # if self.rlog is not None:
        #     fileHandler.insert_video((frame_id, img))

    def draw_obs(self, img, data):
        if len(data) == 0:
            return
        if data['type'] != 'obstacle':
            return

        self.player.show_obs(img, data)
        if self.show_ipm:
            self.player.show_ipm_obs(self.ipm, data)

    def draw_rtk(self, img, data):
        self.player.show_rtk(img, data)
        if len(data) == 0 or data.get('source') is None:
            return
        timestamp = data['ts_origin']
        r = data
        if not self.replay:
            self.hub.fileHandler.insert_raw((timestamp, data['source'] + '.sol',
                                    '{} {} {:.8f} {:.8f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'.format(
                                        r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'],
                                        r['velE'], r['velD'], r['yaw'], r['pitch'], r['length'])))
            self.hub.fileHandler.insert_raw(
                (timestamp, data['source'] + '.dop', '{} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                    r['sat'][0], r['sat'][1], r['sat'][2], r['sat'][3], r['sat'][4], r['sat'][5], r['gdop'],
                    r['pdop'], r['hdop'], r['htdop'], r['tdop'], r['cutoff'], r['trkSatn'], r['prn'])))
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

        # if self.target:
        #     # print(self.set_target)
        #     self.player.show_target(img, self.target, data)

    def draw_rtk_ub482(self, img, data):
        self.player.show_ub482_common(img, data)
        if data['type'] == 'bestpos':
            if not self.replay:
                self.hub.fileHandler.insert_raw((data['ts'], data['source'] + '.bestpos',
                                    '{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                                        data['sol_stat'], data['pos_type'], data['lat'], data['lon'], data['hgt'],
                                        data['undulation'], data['datum'], data['lat_sgm'], data['lon_sgm'],
                                        data['hgt_sgm'],
                                        data['diff_age'], data['sol_age'], data['#SVs'], data['#solSVs'],
                                        data['ext_sol_stat']
                                    )))
        elif data['type'] == 'heading':

            if not self.replay:
                self.hub.fileHandler.insert_raw((data['ts'], data['source'] + '.heading',
                                    '{} {} {} {} {} {} {} {} {} {} {} {}'.format(
                                        data['sol_stat'], data['pos_type'], data['length'], data['yaw'], data['pitch'],
                                        data['hdgstddev'], data['ptchstddev'], data['#SVs'], data['#solSVs'],
                                        data['#obs'], data['#multi'], data['ext_sol_stat']
                                    )))

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

    def draw_vehstate(self, img, data):
        if len(data) == 0:
            return
        if 'speed' in data:
            self.player.show_veh_speed(img, data['speed'], data['source'])
        # self.ego_car.update_dynamics(data)
        if 'yaw_rate' in data:
            self.player.show_yaw_rate(img, data['yaw_rate'], data['source'])
            # self.rtkplot.update('yawr', data['ts'], data['yaw_rate'])
            # self.player.show_host_path(img, data['speed'], data['yaw_rate'])
            # if self.show_ipm:
            #     self.player.show_host_path_ipm(self.ipm, data['speed'], data['yaw_rate'])

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
            self.draw_obs(img, data)
        elif data['type'] == 'lane':
            self.player.draw_lane_r(img, data)
            if self.show_ipm:
                self.player.show_lane_ipm(self.ipm, (data['a0'], data['a1'], data['a2'], data['a3']), data['range'])

        elif data['type'] == 'vehicle_state':
            self.draw_vehstate(img, data)
        elif data['type'] == 'CIPV':
            self.cipv = data['id']
        elif data['type'] == 'rtk':
            data['updated'] = True
            self.draw_rtk(img, data)
        elif data['type'] == 'bestpos':
            self.draw_rtk_ub482(img, data)
        elif data['type'] == 'heading':
            self.draw_rtk_ub482(img, data)
        elif data['type'] == 'rtcm':
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

    def get_alert(self, vehicle_data, lane_data, ped_data):
        alert = {}
        warning_level, alert_ttc, hw_state, fcw_state, vb_state, sg_state = 0, 0, 0, 0, 0, 0
        if vehicle_data:
            speed = vehicle_data['speed']
            focus_index = vehicle_data['focus_index']
            if focus_index != -1:
                fcw_state = vehicle_data['forward_collision_warning']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                hw_state = vehicle_data['headway_warning']
        alert['ttc'] = float(alert_ttc)
        alert['warning_level'] = int(warning_level)
        alert['hw_state'] = int(hw_state)
        alert['fcw_state'] = int(fcw_state)
        alert['vb_state'] = int(vb_state)
        alert['sg_state'] = int(sg_state)

        lane_warning = 0
        speed = 0
        if lane_data:
            lane_warning = lane_data['deviate_state']
            speed = lane_data['speed'] * 3.6
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)

        return alert


if __name__ == "__main__":
    from config.config import load_cfg
    load_cfg('config/cfg_superb.json')
    hub = Hub()
    pcc = PCC(hub, ipm=True, replay=False)
    pcc.start()
