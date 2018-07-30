#!/usr/bin/python
# -*- coding -*-

from multiprocessing import Process
import asyncio
import websockets
import msgpack

class MtkSink(Process):
    def __init__(self, queue):
        Process.__init__(self)
        self.daemon = True
        self.msg_queue = queue

    def run(self):
        asyncio.get_event_loop().run_until_complete(
                self.msg_recv('ws://192.168.1.201:24012', self.msg_queue))

    async def msg_recv(self, uri, msg_queue):
        def pkg_vehicle(data):
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
            return res

        def pkg_lane(data):
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
            return res

        def pkg_ped(data):
            res = dict()
            keys = ["frame_id", "pedestrains", "ped_on", "pcw_on"]
            res = dict(zip(keys, data))
            pedestrains_keys = [
                "detect_box", "regressed_box", "dist", "ttc", "is_danger",
                "is_key", "classify_type", "type_conf", "pcw_overlap",
                "work_overlap", "roi_num"
                 ]
            pedestrains = []
            for pedestrain in res['pedestrains']:
                ddict = dict(zip(pedestrains_keys, pedestrain))
                pedestrains.append(ddict)
            res['pedestrains'] = pedestrains
            return res

        async with websockets.connect(uri) as websocket:
            msg = {
                'source': 'pcview-client',
                'topic': 'subscribe',
                'data': 'debug.hub.*',
            }
            data = msgpack.packb(msg)
            await websocket.send(data)

            while True:
                try:
                    data = await websocket.recv()
                    msg = msgpack.unpackb(data, use_list=False)
                    if msg[b'topic'] == b'debug.hub.ped':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('ped', pkg_ped(data))
                        msg_queue.put(('ped', pkg_ped(data)))
                    if msg[b'topic'] == b'debug.hub.lane':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('lane', pkg_lane(data))
                        msg_queue.put(('lane', pkg_lane(data)))
                    if msg[b'topic'] == b'debug.hub.vehicle':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('vehicle', pkg_vehicle(data))
                        msg_queue.put(('vehicle', pkg_vehicle(data)))

                except websockets.exceptions.ConnectionClosed as err:
                    print('Connection was closed')
                    break
