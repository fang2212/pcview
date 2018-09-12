#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import json
from multiprocessing import Process, Queue, Value

import asyncio
import numpy as np
import cv2

from client.draw.base import BaseDraw, CVColor
from client.draw.ui_draw import Player
from etc.config import config

class DMSView(object):

    @staticmethod
    def dms_sample_func():

        '''
        cv::projectPoints(axes_endpoints,
                        rotation,
                        translation,
                        context.cam_matrix,
                        context.dist_coeffs,
                        axes_endpoints_rep);
        '''

        pass

    @staticmethod
    def DrawFaceModel(show_intrinsic):
        if (show_intrinsic) {
            rotation = context.intrinsic_pose.mat;
            translation = (cv::Mat_<double>(3, 1) << 0.0, 0.0, -10.0);
            display_offset = {-500, 150};
            ftr_pt_color = context.landmarks_stable ? blue : red;
        } else {
            rotation = context.rt_info.rotation.mat;
            translation = context.rt_info.translation_vec;
            display_offset = {0, 0};
            ftr_pt_color = orange;
        }

        // draw axes
        std::vector<cv::Point2f> axes_endpoints_rep;
        cv::projectPoints(axes_endpoints,
                        rotation,
                        translation,
                        context.cam_matrix,
                        context.dist_coeffs,
                        axes_endpoints_rep);
        for (auto &p : axes_endpoints_rep) {
            p += display_offset;
        }

        line(canvas, axes_endpoints_rep[0], axes_endpoints_rep[1], cv::Scalar(0, 0, 255));
        line(canvas, axes_endpoints_rep[0], axes_endpoints_rep[2], cv::Scalar(0, 255, 255));
        line(canvas, axes_endpoints_rep[0], axes_endpoints_rep[3], cv::Scalar(0, 255, 0));

        if (show_intrinsic) {
            // draw face landmarks
            FaceFeaturePoints face_model_rep;
            cv::projectPoints(context.face_model,
                            rotation,
                            translation,
                            context.cam_matrix,
                            context.dist_coeffs,
                            face_model_rep);
            for (auto &&p : face_model_rep) {
                p += display_offset;
                cv::circle(canvas, p, fixed ? 2 : 1, ftr_pt_color, -1);
            }
        }

    }

def draw_dms(img, context):
    '''
    out_text_buf = (
        "#ff00ffBasic:\n"
        "video: %s\n"
        "frame: %d\n"
        "seconds: %.3f\n"
        "fps: %.1f\n"
        "\n#ff00ffDriver:\n"
        "r(h-c): %3.f %3.f %3.f\n"
        "t(h-c): %3.1f %3.1f %3.1f\n"
        "r(c-h): %3.f %3.f %3.f\n"
        "t(c-h): %3.1f %3.1f %3.1f\n"
        "pose: %3.f %3.f %3.f\n"
        "%sStatic: %6.2fs / %.2fs\n"
        "Eye: %6.2f %6.2f\n"
        "\n#ff00ffAlerts:\n"
        "%sEye closure:  %3.f%% %.1fs\n"
        "%sYawn:        %3.f%% %.1fs\n"
        "%sLook up    : %3.f%% %.1fs\n"
        "%sLook around: %3.f%% %.1fs\n"
        "%sLook down  : %3.f%% %.1fs\n"
        "%sPhone call :  %3.f%% %.1fs\n"
        "%sSmoking    : %3.f%% %.1fs\n"
        "%sAbsence    : %3.f%% %.1fs\n") % (
        video_name,
        context.frame.count,
        context.frame.millis * 1e-3,
        context.process_fps,

        context.rt_info.rotation.yaw,
        context.rt_info.rotation.pitch,
        context.rt_info.rotation.roll,
        context.rt_info.translation_vec.at<double>(0, 0),
        context.rt_info.translation_vec.at<double>(1, 0),
        context.rt_info.translation_vec.at<double>(2, 0),

        context.rt_info_inv.rotation.yaw,
        context.rt_info_inv.rotation.pitch,
        context.rt_info_inv.rotation.roll,
        context.rt_info_inv.translation_vec.at<double>(0, 0),
        context.rt_info_inv.translation_vec.at<double>(1, 0),
        context.rt_info_inv.translation_vec.at<double>(2, 0),

        context.intrinsic_pose.yaw,
        context.intrinsic_pose.pitch,
        context.intrinsic_pose.roll,

        (context.longest_static_length < FLAGS_normal_pose_static_threshold ? red_s : white_s).c_str(),
        context.static_length * 1e-3,
        context.longest_static_length * 1e-3,
        context.left_eye_open_faction,
        context.right_eye_open_faction,
        (context.eye_alert.alerting() ? red_s : white_s).c_str(),
        context.eye_alert.score * 100,
        context.eye_alert.duration * 1e-3,
        (context.yawn_alert.alerting() ? red_s : white_s).c_str(),
        context.yawn_alert.score * 100,
        context.yawn_alert.duration * 1e-3,
        (context.look_up_alert.alerting() ? red_s : white_s).c_str(),
        context.look_up_alert.score * 100,
        context.look_up_alert.duration * 1e-3,
        (context.look_around_alert.alerting() ? red_s : white_s).c_str(),
        context.look_around_alert.score * 100,
        context.look_around_alert.duration * 1e-3,
        (context.look_down_alert.alerting() ? red_s : white_s).c_str(),
        context.look_down_alert.score * 100,
        context.look_down_alert.duration * 1e-3,
        (context.phone_alert.alerting() ? red_s : white_s).c_str(),
        context.phone_alert.score * 100,
        context.phone_alert.duration * 1e-3,
        (context.smoking_alert.alerting() ? red_s : white_s).c_str(),
        context.smoking_alert.score * 100,
        context.smoking_alert.duration * 1e-3,
        (context.absence_alert.alerting() ? red_s : white_s).c_str(),
        context.absence_alert.score * 100,
        context.absence_alert.duration * 1e-3
    )
    '''
    '''
    patch::putText(canvas,
                   std::string(out_text_buf),
                   cv::Point(10, 20),
                   font,
                   0.4,
                   white,
                   1,
                   cv::LINE_8,
                   false,
                   16);
    '''

    if context.face_detected:
        DrawFaceModel(false)
        DrawFaceModel(true)
        DrawRect(canvas, context.regression_result.locating_box, -1)
        DrawFeaturePts(canvas,
                       context.regression_result.ftr_pts,
                       context.landmarks_stable,
                       context.eye_alert.alerting() or context.look_down_alert.alerting(),
                       context.yawn_alert.score > 0)

    if context.left_phone_detected:
        DrawRect(canvas, context.left_phone_region, red)
    if context.right_phone_detected:
        DrawRect(canvas, context.right_phone_region, red)
    if context.smoking_detected:
        DrawRect(canvas, context.smoking_region, red)

    # vehicle
def draw_vehicle(self, img, vehicle_data):
    v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
    if vehicle_data:
        focus_index = vehicle_data['focus_index']
        for i, vehicle in enumerate(vehicle_data['dets']):
            focus_vehicle = (i == focus_index)
            position = vehicle['bounding_rect']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Red if focus_index == i else CVColor.Cyan
            self.player.show_vehicle(img, position, color, 2)
            
            self.player.show_vehicle_info(img, position,
                                    vehicle['vertical_dist'],vehicle['horizontal_dist'], 
                                    vehicle['vehicle_width'], str(vehicle['type']))
            if config.show.overlook:
                self.player.show_overlook_vehicle(img, focus_vehicle,
                                            vehicle['vertical_dist'],
                                            vehicle['horizontal_dist'])
            
        if focus_index != -1:
            vehicle = vehicle_data['dets'][focus_index]
            # v_type = vehicle['type']
            # index = vehicle['index']
            ttc = '%.2f' % vehicle['rel_ttc']
            fcw = vehicle_data['forward_collision_warning']
            hw = vehicle_data['headway_warning']
            hwm = '%.2f' % vehicle_data['ttc']
            vb = vehicle_data['bumper_warning']
            if ttc == '1000.00':
                ttc = '-'
    
    para_list = ParaList('vehicle')
    para_list.insert('ttc', ttc)
    para_list.insert('fcw', fcw)
    para_list.insert('hwm', hwm)
    para_list.insert('hw', hw)
    para_list.insert('vb', vb)
    self.player.show_normal_parameters(img, para_list, (100, 0))
    '''
    parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
    self.player.show_vehicle_parameters(img, parameters, (100, 0))
    '''

# lane
def draw_lane(self, img, lane_data):
    lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
    if lane_data:
        speed = lane_data['speed']
        deviate_state = lane_data['deviate_state']
        for lane in lane_data['lanelines']:
            if ((int(lane['label']) in [1, 2]) or config.show.all_laneline)and speed >= config.show.lane_speed_limit:
                # color = CVColor.Cyan
                color = CVColor.Blue
                width = lane['width']
                l_type = lane['type']
                conf = lane['confidence']
                index = lane['label']
                #print('label', index, deviate_state)
                if int(index) == int(deviate_state):
                    color = CVColor.Red
                self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                                        0.2, color)
                if config.show.overlook:
                    self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                self.player.show_lane_info(img, lane['perspective_view_poly_coeff'],
                                            index, width, l_type, conf, color)

        lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
        rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
        ldw = lane_data['deviate_state']
        trend = lane_data['deviate_trend']
        if lw_dis == '111.00':
            lw_dis = '-'
        if rw_dis == '111.00':
            rw_dis = '-'

    para_list = ParaList('lane')
    para_list.insert('lw_dis', lw_dis)
    para_list.insert('rw_dis', rw_dis)
    para_list.insert('ldw', ldw)
    para_list.insert('trend', trend)
    self.player.show_normal_parameters(img, para_list, (192, 0))
    '''
    parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
    self.player.show_lane_parameters(img, parameters, (200, 0))
    '''

# ped
def draw_ped(self, img, ped_data):
    pcw_on, ped_on = '-', '-'
    if ped_data:
        if ped_data.get('pcw_on'):
            pcw_on = 1
        if ped_data.get('ped_on'):
            ped_on = 1
        for pedestrain in ped_data['pedestrians']:
            position = pedestrain['regressed_box']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Yellow
            if pedestrain['is_key']:
                color = CVColor.Pink
            if pedestrain['is_danger']:
                color = CVColor.Pink
            self.player.show_peds(img, position, color, 2)
            if position[0] > 0:
                self.player.show_peds_info(img, position, pedestrain['dist'])
    para_list = ParaList('ped')
    para_list.insert('pcw_on', pcw_on)
    #para_list.insert('ped_on', ped_on)
    self.player.show_normal_parameters(img, para_list, (430, 0))

def draw_tsr(self, img, tsr_data):
    focus_index, speed_limit, tsr_warning_level, tsr_warning_state = -1, 0, 0, 0
    if tsr_data:
        focus_index = tsr_data['focus_index']
        speed_limit = tsr_data['speed_limit']
        tsr_warning_level = tsr_data['tsr_warning_level']
        tsr_warning_state = tsr_data['tsr_warning_state']
        for i, tsr in enumerate(tsr_data['dets']):
            position = tsr['position']
            position = position['x'], position['y'], position['width'], position['height']
            color = CVColor.Red
            self.player.show_tsr(img, position, color, 2)
            if tsr['max_speed'] != 0:
                self.player.show_tsr_info(img, position, tsr['max_speed'])                

    para_list = ParaList('tsr')
    para_list.insert('speed_limit', speed_limit)
    self.player.show_normal_parameters(img, para_list, (305, 0))
    # parameters = [str(focus_index), str(speed_limit), str(tsr_warning_level), str(tsr_warning_state)]
    # self.player.show_tsr_parameters(img, parameters, (300, 0))


def draw_mobile(self, img, mobile_log):
    # mobile_log = None
    if mobile_log:
        mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
        mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
        mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
        mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
        mobile_pcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('peds_fcw') == 1 else 0
        mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
        mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0
        para_list = ParaList('mobile')
        para_list.insert('hwm', mobile_hwm)
        para_list.insert('hw', mobile_hw)
        para_list.insert('fcw', mobile_fcw)
        para_list.insert('vb', mobile_vb)
        para_list.insert('ldw', mobile_ldw)
        para_list.insert('pcw', mobile_pcw)
        self.player.show_normal_parameters(img, para_list, (300, 0))
        '''
        mobile_parameters = [str(mobile_hwm), str(mobile_hw), str(mobile_fcw), str(mobile_vb), str(mobile_ldw), str(mobile_pcw)]
        self.player.show_mobile_parameters(img, mobile_parameters, (600, 0))
        '''
