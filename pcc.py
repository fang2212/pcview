#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'pengquanhua <pengquanhua@minieye.cc>'
__version__ = '0.1.0'
__progname__ = 'run'

from config.config import *
import cv2
import logging
from tools.transform import calc_g2i_matrix
from datetime import datetime
from player.pcc_ui import Player
from sink.hub import Hub


class PCC():
    def __init__(self, hub):
        self.hub = hub
        self.exit = False
        # self.recording = False
        self.player = Player()
        self.now_id = 0
        self.pre_lane = {}
        self.pre_vehicle = {}
        self.pre_ped = {}
        self.pre_tsr = {}
        self.vis_pos = {}
        self.vis_lane = {}
        self.ts_now = 0
        self.msg_cnt = {}
        self.m_g2i = calc_g2i_matrix()
        self.set_target = False
        self.target = None
        self.ipm = None

    def start(self):
        self.hub.start()
        self.player.start_time = datetime.now()
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop_simple()
            if d is None:
                continue
            if not d.get('frame_id'):
                continue
            frame_cnt += 1
            self.draw(d, frame_cnt)
            if frame_cnt >= 200:
                self.player.start_time = datetime.now()
                frame_cnt = 0

    def fix_frame(self, pre_, now_, fix_range):
        if now_.get('frame_id') or (not fix_range):
            return now_, now_
        if pre_.get('frame_id'):
            if pre_.get('frame_id') + fix_range >= self.now_id:
                return pre_, pre_
        return {}, {}

    def draw(self, mess, frame_cnt):
        # print('draw')
        # print(mess)
        img = mess['img']
        frame_id = mess['frame_id']
        self.now_id = frame_id
        # vehicle_data = mess['vehicle']
        # lane_data = mess['lane']
        # ped_data = mess['ped']
        # tsr_data = mess['tsr']
        # can_data = mess['can']
        # can1_data = mess['can1']
        # can2_data = mess['can2']
        # can3_data = mess['can3']
        # print(len(img))

        if config.save.video:
            self.hub.fileHandler.insert_video((frame_id, img.copy()))

        self.ipm = cv2.warpPerspective(img, self.m_g2i, (480, 720))

        # if img is None:
        #     return
        if config.show.overlook:
            self.player.show_overlook_background(img)


        if config.mobile.show:
            bg_width = 120 * 6
        else:
            bg_width = 120 * 4

        self.player.show_columns(img)

        self.player.show_frame_id(img, frame_id)
        self.player.show_datetime(img, self.ts_now)

        # if config.work_mode == 'validator':
        #     self.player.show_parameters_background(img, (0, 0, bg_width + 20, 150))
        #
        # else:
        #     self.player.show_parameters_background(img, (0, 0, 120 * 2 + 20, 150))

            # fix frame
            # self.pre_lane, lane_data = self.fix_frame(self.pre_lane, lane_data, config.fix.lane)
            # self.pre_vehicle, vehicle_data = self.fix_frame(self.pre_vehicle, vehicle_data, config.fix.vehicle)
            # self.pre_ped, ped_data = self.fix_frame(self.pre_ped, ped_data, config.fix.ped)
            # self.pre_tsr, tsr_data = self.fix_frame(self.pre_tsr, tsr_data, config.fix.tsr)

        if config.show.vehicle:
            if 'vehicle' in mess and mess['vehicle']:
                self.hub.msg_cnt['vehicle']['fix'] += 1
                self.player.draw_vehicle(img, mess['vehicle'])

        if config.show.lane:
            if 'lane' in mess and mess['lane']:
                self.hub.msg_cnt['lane']['fix'] += 1
                self.player.draw_lane(img, mess['lane'])

        if config.show.ped:
            if 'ped' in mess and mess['ped']:
                self.hub.msg_cnt['ped']['fix'] += 1
                self.player.draw_ped(img, mess['ped'])

        if config.show.tsr:
            if 'tsr' in mess and mess['tsr']:
                self.hub.msg_cnt['tsr']['fix'] += 1
                self.player.draw_tsr(img, mess['tsr'])

        if 'can' in mess and mess['can']:
            # print('can0 data')
            for d in mess['can']:
                self.ts_now = d['ts']
                self.player.draw_can_data(img, d, self.ipm)

        if 'rtk' in mess and mess['rtk']:
            for d in mess['rtk']:
                self.player.draw_rtk(img, d)
                if self.set_target:
                    self.target = {'lat': d['lat'], 'lon': d['lon'], 'hgt': d['hgt'], 'rtkst': d['rtkst']}
                    self.hub.fileHandler.insert_raw((d['ts'], 'rtkpin', '{} {} {} {}'.format(
                        d['rtkst'], d['lat'], d['lon'], d['hgt'])))
                    self.set_target = False


        # if can1_data:
        #     for d in can1_data:
        #         self.ts_now = d['ts']
        #         self.draw_can_data(img, d)
        #
        # if can2_data:
        #     # print('can2 data')
        #     for d in can2_data:
        #         self.ts_now = d['ts']
        #         self.draw_can_data(img, d)
        #
        # if can3_data:
        #     for d in can3_data:
        #         self.ts_now = d['ts']
        #         self.draw_can_data(img, d)
        #
        if self.hub.fileHandler.recording:
            self.player.show_recording(img, self.hub.fileHandler.start_time)

        logging.debug('msg state {}'.format(self.hub.msg_cnt))

        # show env info
        light_mode = -1
        if 'vehicle' in mess and mess['vehicle']:
            light_mode = mess['vehicle']['light_mode']
            speed = mess['vehicle'].get('speed') if mess['vehicle'].get('speed') else 0
            speed = mess['lane'].get('speed') * 3.6 if mess['lane'].get('speed') else speed

        fps = self.player.cal_fps(frame_cnt)
        # self.player.show_env(img, self.speed, light_mode, fps, (0, 0))
        self.player.show_fps(img, fps)
        # save info
        if config.save.alert:
            alert = self.get_alert(mess['vehicle'], mess['lane'], mess['ped'])
            self.hub.fileHandler.insert_alert((frame_id, {frame_id: alert}))
            self.hub.fileHandler.insert_image((frame_id, img))

        if config.save.log:
            temp_mess = mess
            temp_mess.pop('img')
            self.hub.fileHandler.insert_log((frame_id, temp_mess))

        # draw_corners(img)
        cv2.imshow('UI', img)
        cv2.imshow('IPM', self.ipm)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            self.exit = True
        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True
        elif key == ord('r'):
            if self.hub.fileHandler.recording:
                # self.recording = False
                self.hub.fileHandler.stop_rec()
            else:
                # self.recording = True
                self.hub.fileHandler.start_rec()
            print('toggle recording status. {}'.format(self.hub.fileHandler.recording))
        elif key == ord('d'):
            self.set_target = True

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
        if lane_data:
            lane_warning = lane_data['deviate_state']
            speed = lane_data['speed'] * 3.6
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)

        return alert


if __name__ == "__main__":
    hub = Hub()
    pcc = PCC(hub)
    pcc.start()
