import os
import cv2
from datetime import datetime

pack = os.path.join


def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)


def get_video_str():
    now = datetime.now()
    FORMAT = 'rec_%Y%m%d%H%M_'
    return now.strftime(FORMAT) + str(now.microsecond).zfill(6)


class Recorder(object):
    def __init__(self, path=''):
        self._path = path
        self._writer = None

        if not os.path.exists(self._path):
            os.makedirs(self._path)

    def set_writer(self):
        pass

    def write(self, data):
        self._writer.write(data)

    def release(self):
        pass


class VideoRecorder(Recorder):
    def __init__(self, path, fps=20):
        Recorder.__init__(self, path)
        self.fps = fps
        self._fid_writer = None
        self._video_writer = None
        self._cnt = 0

    def set_writer(self, w=1280, h=720, file_name=None):
        if not file_name:
            file_name = get_data_str()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._video_writer = cv2.VideoWriter(pack(self._path, file_name + '.avi'),
                                             fourcc, self.fps, (w, h), True)
        self._fid_writer = open(pack(self._path, file_name + '.txt'), 'w+')

    def write(self, data):
        """
        {
            'ts': timestamp,
            'fid': frame_id,
            'image': image,
            'msg_type': msg_type
        }
        """
        ts, fid, image = data['ts'], data['fid'], data['image']
        ts = int(ts * 1000000)
        txt = '%s %s %s' % (ts // 1000000, ts % 1000000, fid)
        self._fid_writer.write(txt + '\n')
        self._video_writer.write(image)
        self._cnt += 1
        if self._cnt % 2:
            self._fid_writer.flush()
        if self._cnt % 200 == 0:
            self.release()
            self.set_writer()

    def release(self):
        self._video_writer.release()
        self._fid_writer.release()


class TextRecorder(Recorder):
    def __init__(self, path):
        Recorder.__init__(self, path)
        self._cnt = 0

    def set_writer(self, file_name=None):
        if not file_name:
            file_name = get_data_str()
        self._writer = open(pack(self._path, file_name), 'w+')
        self._cnt = 0

    def write(self, data):
        self._writer.write(data)
        self._cnt += 1
        if self._cnt % 100 == 0:
            self._writer.flush()

    def release(self):
        self._writer.close()


class CanRecorder(TextRecorder):
    def __init__(self, path):
        TextRecorder.__init__(self, path)

    def write(self, data):
        """
        {
            'ts': timestamp,
            'id': can_id,
            'data': data,
            'msg_type': msg_type,
        }
        """
        ts, can_id = data['ts'], data['can_id']
        data, msg_type = data['data'], data['msg_type']
        ts = int(ts * 1000000)
        txt = '%s %s ' % (ts // 1000000, ts % 1000000)
        txt += '%s 0x%x ' % (str(msg_type), can_id)
        txt += '%02X %02X %02X %02X %02X %02X %02X %02X' % (data[0], data[1],
                                                            data[2], data[3],
                                                            data[4], data[5],
                                                            data[6], data[7])
        self._writer.write(txt + '\n')
        self._cnt += 1
        if self._cnt % 100 == 0:
            self._writer.flush()


class GsensorRecorder(TextRecorder):
    def __init__(self, path):
        TextRecorder.__init__(self, path)

    def write(self, data):
        """
        {
            'ts': timestamp,
            'accl': accl,
            'gyro': gyro,
            'temp': temp,
            'sec': sec,
            'usec': usec,
            'msg_type': msg_type
        }
        """
        ts = data['ts']
        accl = data['accl']
        gyro = data['gyro']
        temp = data['temp']
        sec = data['sec']
        usec = data['usec']
        ts = int(ts * 1000000)
        txt = '%s %s ' % (ts // 1000000, ts % 1000000)
        txt += '%s ' % ('gsensor')
        txt += '{} {} {} {} {} {} {:.6f} {} {}'.format(accl[0], accl[1], accl[2],
                                                       gyro[0], gyro[1], gyro[2],
                                                       temp, sec, usec)
        self._writer.write(txt + '\n')
        self._cnt += 1
        if self._cnt % 100 == 0:
            self._writer.flush()
