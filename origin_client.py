#!/usr/bin/python
# -*- coding:utf8 -*-


import threading
import nanomsg
import msgpack
import json


class Sink(threading.Thread):# 继承线程类

    def __init__(self, ip, port=1200):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self._init_socket()
        self.cur_frame_id = -1
        self._data_queue = []
        self._cv = threading.Condition()

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self):
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])
            #if len(self._data_queue) > 0 and frame_id < self._data_queue[-1][0]:
            #    continue
            self._data_queue.append((frame_id, data, ))
            with self._cv:
                self._cv.notify()

    def pkg_handler(self, msg_buf):
        pass

    def set_frame_id(self, frame_id):
        # This method must be called
        self.cur_frame_id = frame_id

    def deq(self, block=False):
        if block:
            with self._cv:
                while len(self._data_queue) <= 0:
                    self._cv.wait()
                frame_id, data = self._data_queue.pop(0)
                return frame_id, data
        if len(self._data_queue) <= 0:
            return -1, None
        frame_id, data = self._data_queue.pop(0)
        return frame_id, data


class CameraSink(Sink):

    def __init__(self, ip, port=1200):
        Sink.__init__(self, ip, port)

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[16:]
        return frame_id, data


class LaneSink(Sink):

    def __init__(self, ip, port=1203):
        Sink.__init__(self, ip, port)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        self.set_frame_id(data[0])
        frame_id = data[0]
        res = dict()
        keys = [
            "frame_id", "deviate_state", "lanelines", "turn_radius",
            "speed_thresh", "turn_frequently", "left_wheel_dist",
            "right_wheel_dist", "warning_dist", "lateral_speed",
            "earliest_dist", "latest_dist", "deviate_trend",
            "success", "speed", "left_lamp", "right_lamp"]
        res = dict(zip(keys, data))
        line_keys = [
            "bird_view_poly_coeff", "perspective_view_poly_coeff",
            "confidence", "warning", "label", "color", "type", "width", "start", "end",
            "bird_view_pts"]
        lines = []
        for line in res["lanelines"]:
            ldict = dict(zip(line_keys, line))
            lines.append(ldict)
        res["lanelines"] = lines
        return frame_id, res


class VehicleSink(Sink):

    def __init__(self, ip, port=1204):
        Sink.__init__(self, ip, port)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        self.set_frame_id(data[0])
        frame_id = data[0]
        res = dict()
        keys = [
            "frame_id", "dets", "focus_index", "light_mode", "weather", "wiper_on",
            "ttc", "forward_collision_warning", "headway_warning", "bumper_warning",
            "stop_and_go_warning", "warning_level", "warning_vehicle_index",
            "bumper_running", "bumper_state", "stop_and_go_state", "speed", "radius"]
        res = dict(zip(keys, data))
        det_keys = [
            "vertical_dist", "horizontal_dist", "ttc", "rel_ttc", "rel_speed",
            "speed_acc", "vehicle_width", "det_confidence", "rect", "bounding_rect",
            "index", "type", "warning_level", "count", "is_close", "on_route"]
        dets = []
        for det in res["dets"]:
            ddict = dict(zip(det_keys, det))
            dets.append(ddict)
        res["dets"] = dets
        return frame_id, res


class Hub(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._sinks = []
        self.elms = []
        self._flag_start = False
        self._cur_frame_id = []
        self._num_sink = -1
        self._init_frame_done = False
        self._cv = threading.Condition()

    def add_sink(self, sink):
        if not self._flag_start:
            self._sinks.append(sink)

    def _add_sink_done(self):
        self._flag_start = True
        self._cur_frame_id = [-1] * len(self._sinks)
        self._num_sink = len(self._sinks)

    def check_ready(self):
        if len(self.elms) <= 0:
            return False
        for fid in self._cur_frame_id:
            if fid == -1 or fid < self.elms[0][0]:
                return False
        return True

    def start_main_loop(self):
        self._add_sink_done()
        self.start()

    def run(self):
        while True:
            self.init_frame()
            self.run_frame()

    def init_frame(self):
        if self._init_frame_done:
            return
        self._init_frame_done = True

        for i, fid in enumerate(self._cur_frame_id):
            frame_id, data = -1, None
            if fid == -1:
                frame_id, data = self._sinks[i].deq(block=True)

            self._cur_frame_id[i] = frame_id

            ind = -1
            for j, elm in enumerate(self.elms):
                if frame_id <= elm[0]:
                    ind = j
                    break

            if ind == -1:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.append(elm)
                continue

            if frame_id == self.elms[j][0]:
                self.elms[j][i + 1] = data
            else:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.insert(j, elm)

    def run_frame(self):
        for i, sink in enumerate(self._sinks):
            frame_id, data = sink.deq()
            if frame_id < 0:
                return
            self._cur_frame_id[i] = frame_id

            ind = -1
            for j, elm in enumerate(self.elms):
                if frame_id <= elm[0]:
                    ind = j
                    break

            if ind == -1:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.append(elm)
                continue

            if frame_id == self.elms[j][0]:
                self.elms[j][i + 1] = data
            else:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.insert(j, elm)

        if self.check_ready():
            with self._cv:
                self._cv.notify()

    def deq(self):
        # Should be a blocking method
        if len(self.elms) <= 0 or not self.check_ready():
            with self._cv:
                self._cv.wait()
        elm = self.elms.pop(0)
        return {"frame_id": elm[0], "data": elm[1:]}


class WorkHub(Hub):
    def __init__(self, ip):
        Hub.__init__(self)
        camera_sink = CameraSink(args.ip, 1200)
        lane_sink = LaneSink(args.ip, 1203)
        vehicle_sink = VehicleSink(args.ip, 1204)
        self.add_sink(camera_sink)
        self.add_sink(lane_sink)
        self.add_sink(vehicle_sink)
        camera_sink.start()
        lane_sink.start()
        vehicle_sink.start()
        self.start_main_loop()


import numpy as np
import cv2
class PCViewer():

    def __init__(self, ip):
        self.hub = WorkHub(ip)

    def draw(self):
        log_fp = open('out/log.json', 'w+')
        cnt = 0
        res_data = []
        while True:
            if cnt > 6000:
                log_fp.write(json.dumps(res_data))
                log_fp.close()
                print('write ok')
                return
            d = self.hub.deq()
            print(d["frame_id"])
            frame_id = d["frame_id"]
            image_data = d["data"][0]
            lane_data = d["data"][1]
            print(lane_data)
            vehicle_data = d["data"][2]
            print(vehicle_data)
            if len(image_data) <= 0:
                continue
            if len(vehicle_data) <= 0:
                continue
            cnt += 1
            
            output_data = {
                'frame_id': frame_id,
                'lane_data': lane_data,
                'vehicle_data': vehicle_data
            }

            # log_fp.write(str(output_data)+'\n')
            res_data.append(output_data)
            image = np.fromstring(image_data, dtype=np.uint8).reshape(720, 1280, 1)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            self.draw_lane(image, lane_data)
            cv2.imwrite('out/'+ str(frame_id) + '.jpg', image)
            cv2.imshow("pcviewer", image)
            cv2.waitKey(1)

    def draw_lane(self, image, lane_data):
        if len(lane_data) > 0:
            for lane_line in lane_data["lanelines"]:
                self.draw_curve(lane_line["perspective_view_poly_coeff"], image, (0, 255, 0), 450, 700, 10, 1)

    def draw_curve(self, coeffs, image, color, start_y, end_y, resolution, thickness):
        mapint = lambda l: tuple(map(int, l))
        pre_pt = (-1, -1, )
        y = start_y
        while y < end_y:
            x = 0
            for c in coeffs[::-1]:
                x = x * y + c

            cur_pt = (x, y, )

            if x < 0 or x > 1280 or y < 0 or y > 720:
                pre_pt = (-1, -1, )

            if pre_pt[0] > 0:
                cv2.line(image, mapint(pre_pt), mapint(cur_pt), color, thickness)
            y += resolution
            pre_pt = cur_pt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="ip address",
                        type=str)
    args = parser.parse_args()
    PCViewer(args.ip).draw()
