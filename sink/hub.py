from multiprocessing import Queue, Process
from sink.pcc_sink import *
import sys
import websockets
import asyncio
from recorder.FileHandler import FileHandler
import numpy as np
import cv2


class Hub(Process):

    def __init__(self):

        # msg_types = config.msg_types
        image_list_path = config.pic.path

        Process.__init__(self)
        # self.use_camera = True

        self.msg_queue = Queue()
        self.cam_queue = Queue()
        # self.sink = {}
        self.cache = {}

        self.msg_cnt = {}
        msg_types = []
        self.last_res = {}

        finder = ColletorFinder()
        finder.start()
        for i in range(3):
            # try:
            finder.request()
            # except Exception as e:
            #     pass
            time.sleep(0.2)

        print('Devices found:')
        for dev in finder.found:
            print(dev, finder.found[dev])

        print('Connecting to device(s)...')
        # print('collector0 on {}, types:'.format(config.ip), config.msg_types)
        # print('collector1 on {}, types:'.format(config2.ip), config2.msg_types)

        if config.save.log or config.save.alert or config.save.video:
            self.fileHandler = FileHandler()
            self.fileHandler.start()
            self.fileHandler.start_rec()

        self.rtk_sink = RTKSink(self.msg_queue, 0, 0, 'rtk', 0, self.fileHandler)
        self.rtk_sink.start()

        if config.platform == 'fpga':
            if len(finder.found) > 1:
                for ip in finder.found:
                    if finder.found[ip]['mac'] == configs[0].mac:
                        self.camera_sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200,
                                                      msg_type='camera', fileHandler=self.fileHandler)
                        self.camera_sink.start()
                        msg_types += self.fpga_handle(configs[0].msg_types, self.msg_queue, ip, index=0)
                        print('Connected #0 on {}, types:'.format(ip), configs[0].msg_types)
                    elif finder.found[ip]['mac'] == configs[1].mac:
                        msg_types += self.fpga_handle(configs[1].msg_types, self.msg_queue, ip, index=1)
                        print('Connected #1 on {}, types:'.format(ip), configs[1].msg_types)
                    else:
                        msg_types += self.fpga_handle(configs[1].msg_types, self.msg_queue, ip, index=1)

            elif len(finder.found) == 1:
                ip = list(finder.found.keys())[0]
                self.camera_sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200,
                                              msg_type='camera', fileHandler=self.fileHandler)
                self.camera_sink.start()
                msg_types += self.fpga_handle(config.msg_types, self.msg_queue, ip, index=0)
                print('Connected #0 on {}, types:'.format(ip), config.msg_types)
            else:
                print('no device found. use default.')
                msg_types += self.fpga_handle(config.msg_types, self.msg_queue, config.ip, index=0)
                self.camera_sink = CameraSink(queue=self.cam_queue, ip=config.ip, port=1200,
                                              msg_type='camera', fileHandler=self.fileHandler)
                self.camera_sink.start()
            print('msg_types:', msg_types)

        elif config.platform == 'arm':
            logging.debug('arm platform')
            self.arm_handle(config.msg_types, self.msg_queue, config.ip)

        if config.pic.use:
            image_fp = open(image_list_path, 'r+')
            self.image_list = image_fp.readlines()
            image_fp.close()

        msg_types = ['can', 'gsensor', 'rtk']

        self.max_cache = len(msg_types) * 10

        for msg_type in msg_types:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'rev': 0,
                'show': 0,
                'fix': 0,
            }
        self.msg_cnt['frame'] = 0

        # if not config.pic.use:
        #     self.camera_sink = CameraSink(queue=self.cam_queue, ip=config.ip, port=1200, msg_type='camera')
        #     self.camera_sink.start()

    async def arm_flow(self, uri, msg_queue, msg_types):
        async with websockets.connect(uri) as websocket:
            msg = {
                'source': 'pcview-client',
                'topic': 'subscribe',
                'data': 'debug.hub.*',
            }
            data = msgpack.packb(msg)
            await websocket.send(data)
            # print('msg', msg_types)

            while True:
                try:
                    data = await websocket.recv()
                    # print('msg1')
                    msg = msgpack.unpackb(data, use_list=False)
                    for msg_type in msg_types:
                        topic = msg[b'topic'].decode('ascii')
                        if topic == 'debug.hub.' + msg_type:
                            data = msgpack.unpackb(msg[b'data'], use_list=False)
                            data = convert(data)
                            msg_queue.put((data['frame_id'], data, msg_type))

                except websockets.exceptions.ConnectionClosed as err:
                    print('Connection was closed')
                    break

    def arm_handle(self, msg_types, msg_queue, ip):
        def msg_run(msg_queue, msg_types, ip):
            uri = 'ws://' + ip + ':24012'
            logging.debug('uri {}'.format(uri))
            asyncio.get_event_loop().run_until_complete(
                self.arm_flow(uri, msg_queue, msg_types))

        msg_process = Process(target=msg_run,
                              args=(msg_queue, msg_types, ip,))
        msg_process.daemon = True
        msg_process.start()
        return msg_process

    def fpga_handle(self, msg_types, msg_queue, ip, index=0):
        sink = {}
        if 'lane' in msg_types:
            sink['lane'] = LaneSink(queue=msg_queue, ip=ip, port=1203, msg_type='lane')
            sink['lane'].start()

        if 'vehicle' in msg_types:
            sink['vehicle'] = VehicleSink(queue=msg_queue, ip=ip, port=1204, msg_type='vehicle')
            sink['vehicle'].start()

        if 'ped' in msg_types:
            sink['ped'] = PedSink(queue=msg_queue, ip=ip, port=1205, msg_type='ped')
            sink['ped'].start()

        if 'tsr' in msg_types:
            sink['tsr'] = TsrSink(queue=msg_queue, ip=ip, port=1206, msg_type='tsr')
            sink['tsr'].start()

        if 'can0' in msg_types:
            typestr = 'can' + '{:01d}'.format(index * 2)
            sink[typestr] = CANSink(queue=msg_queue, ip=ip, port=1207, msg_type=typestr,
                                    type=configs[index].can_types.can0,
                                    index=index, fileHandler=self.fileHandler)
            sink[typestr].start()

        if 'can1' in msg_types:
            typestr = 'can' + '{:01d}'.format(index * 2 + 1)
            sink[typestr] = CANSink(queue=msg_queue, ip=ip, port=1208, msg_type=typestr,
                                    type=configs[index].can_types.can1,
                                    index=index, fileHandler=self.fileHandler)
            sink[typestr].start()

        if 'gsensor' in msg_types:
            sink['gsensor'] = GsensorSink(queue=msg_queue, ip=ip, port=1209, msg_type='gsensor',
                                          index=index, fileHandler=self.fileHandler)
            sink['gsensor'].start()

        return [i for i in sink]

    def list_len(self):
        length = 0
        for key in self.cache:
            length += len(self.cache[key])
        return length

    def all_has(self):
        for key in self.cache:
            if not self.cache[key]:
                return False
        return True

    def all_over(self, frame_id):
        for key in self.cache:
            if not self.cache[key]:
                # print(self.cache)
                return False
            if self.cache[key][-1][0] < frame_id:
                return False
        return True

    def msg_async(self):
        while not self.msg_queue.empty():
            frame_id, msg_data, msg_type = self.msg_queue.get()
            logging.debug('queue id {}, type {}'.format(frame_id, msg_type))
            self.cache[msg_type].append((frame_id, msg_data))
            self.msg_cnt[msg_type]['rev'] += 1
        time.sleep(0.02)

    def pop_simple(self):
        res = {}
        if not self.cam_queue.empty():
            frame_id, data, msg_type = self.cam_queue.get()
            res['img'] = cv2.imdecode(np.fromstring(data['img'], np.uint8), cv2.IMREAD_COLOR)
            res['frame_id'] = frame_id
            #for key in self.last_res:
             #   res[key] = self.last_res[key]
            for key in self.cache:
                if len(self.cache[key]) > 0:
                    #self.last_res[key] = self.cache[key]
                    res[key] = self.cache[key]
                self.cache[key] = []
            self.msg_cnt['frame'] += 1
            return res
        if not self.msg_queue.empty():
            frame_id, msg_data, msg_type = self.msg_queue.get()
            # res[msg_type] = msg_data
            # res['frame_id'] = frame_id
            if isinstance(msg_data, list):
                # print('msg data list')
                self.cache[msg_type].extend(msg_data)
            elif isinstance(msg_data, dict):
                self.cache[msg_type].append(msg_data)
            self.msg_cnt[msg_type]['rev'] += 1
            self.msg_cnt[msg_type]['show'] += 1

        # return res

    def pop(self):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr': {},
            'can0': {},
            'can1': {},
            'extra': {}
        }

        if config.pic.use:
            while not self.all_has() and self.list_len() <= self.max_cache:
                self.msg_async()
            frame_id = sys.maxsize
            for key in self.cache:
                if self.cache[key]:
                    temp_id = self.cache[key][0][0]
                    # logging.debug('temp id {}'.format(temp_id))
                    frame_id = min(temp_id, frame_id)

            logging.debug('frame_id {}'.format(frame_id))

            index = ((frame_id // 3) * 4 + frame_id % 3) % len(self.image_list)
            image_path = self.image_list[index]
            res['extra'] = {
                'image_path': image_path
            }
            image_path = image_path.strip()
            img = cv2.imread(image_path)
            if config.show.color == 'gray':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            res['img'] = img
        else:
            while True:
                if not self.cam_queue.empty():
                    frame_id, image_data, msg_type = self.cam_queue.get()
                    # image = np.fromstring(image_data, dtype=np.uint8).reshape(720, 1280, 1)
                    # image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                    image = cv2.imdecode(np.fromstring(image_data, np.uint8), cv2.IMREAD_COLOR)

                    res['img'] = image

                    break
                time.sleep(0.02)
            logging.debug('show cam id {}'.format(frame_id))
            # while not self.all_over(frame_id) and self.list_len() < self.max_cache:
            self.msg_async()
            # print('msg_async')
        # print(res)
        logging.debug('out')
        res['frame_id'] = frame_id
        logging.debug('end0 res')

        for key in self.cache:
            if key == 'can0' or key == 'can1':
                while self.cache[key]:
                    res[key] = self.cache[key][0][1]
                    self.msg_cnt[key]['show'] += 1
                    self.cache[key].pop(0)
            while self.cache[key] and self.cache[key][0][0] <= frame_id:
                if self.cache[key][0][0] == frame_id:
                    res[key] = self.cache[key][0][1]
                    self.msg_cnt[key]['show'] += 1
                    self.cache[key].pop(0)
                    # print(frame_id)
                    break
                else:
                    self.cache[key].pop(0)

        self.msg_cnt['frame'] += 1
        # logging.debug('end res {}'.format(res))
        logging.debug('end res ped{}'.format(res['ped']))
        logging.debug('end res tsr{}'.format(res['tsr']))
        return res
