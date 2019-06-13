import os
import threading
import functools
from multiprocessing.dummy import Process as Thread
from config.config import install
from tools.transform import Transform
import time


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


class OrientTuner(object):

    def __init__(self, y=install['video']['yaw'], p=install['video']['pitch'], r=install['video']['roll'],  ey=install['esr']['yaw']):
        self.yaw = y
        self.pitch = p
        self.roll = r
        self.esr_yaw = ey
        self.transform = Transform()

    def update_yaw(self, x):
        self.yaw = install['video']['yaw'] - 0.01 * (x - 500)
        # self.pitch = install['video']['pitch']
        # self.roll = install['video']['roll']

        self.transform.update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_pitch(self, x):
        # self.yaw = install['video']['yaw']
        self.pitch = install['video']['pitch'] - 0.01 * (x - 500)
        # self.roll = install['video']['roll']

        self.transform.update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_roll(self, x):
        # self.yaw = install['video']['yaw']
        self.roll = install['video']['roll'] - 0.01 * (x - 500)
        # self.roll = install['video']['roll']

        self.transform.update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def update_esr_yaw(self, x):
        self.esr_yaw = install['esr']['yaw'] - 0.01 * (x - 500)
        # self.pitch = install['video']['pitch']
        # self.roll = install['video']['roll']

        self.transform.update_m_r2i(self.yaw, self.pitch, self.roll)
        print('current yaw:{} pitch:{} roll:{}'.format(self.yaw, self.pitch, self.roll))

    def save_para(self):
        install['video']['yaw'] = self.yaw
        install['video']['pitch'] = self.pitch
        install['video']['roll'] = self.roll


def sort_big_file(filename, file_splits=10, my_cmp=None):
    idx = 0
    buf_file = []
    buf_path = []
    path = os.path.dirname(filename)
    with open(filename, 'r') as rf:
        for line in rf:
            line = line.strip()
            if line == '':
                continue
            if idx < file_splits:
                bak_path = os.path.join(path, str(idx)+'.tmp.bak')
                buf_file.append(open(bak_path, 'w'))
                buf_path.append(bak_path)
            print(line, file=buf_file[idx % file_splits])
            idx += 1
        for f in buf_file:
            f.flush()
            f.close()
    if my_cmp is None:
        my_cmp = lambda x, y: -1 if x < y else 1

    def sort_one_file(p):
        with open(p, 'r') as rrf:
            lns = rrf.readlines()
            lns.sort(key=functools.cmp_to_key(my_cmp))
        with open(p, 'w') as wf:
            wf.writelines(lns)
    ths = []
    for p in buf_path:
        t = threading.Thread(target=sort_one_file, args=(p,))
        t.start()
        ths.append(t)
    for t in ths:
        t.join()
    merge_times = 0
    while len(buf_path) > 1:
        now_path = os.path.join(path, 'merge-times-' +
                                str(merge_times) + '.tmp.bak')
        now_file = open(now_path, 'w')
        path_one = buf_path.pop(0)
        path_two = buf_path.pop(0)
        file_one = open(path_one, 'r')
        file_two = open(path_two, 'r')
        line_one = next(file_one, None)
        line_two = next(file_two, None)
        while not line_one is None and not line_two is None:
            if my_cmp(line_one, line_two) < 0:
                print(line_one.strip(), file=now_file)
                line_one = next(file_one, None)
            else:
                print(line_two.strip(), file=now_file)
                line_two = next(file_two, None)
        while not line_one is None:
            print(line_one.strip(), file=now_file)
            line_one = next(file_one, None)
        while not line_two is None:
            print(line_two.strip(), file=now_file)
            line_two = next(file_two, None)
        file_one.close()
        file_two.close()
        now_file.close()
        buf_path.append(now_path)
        os.remove(path_one)
        os.remove(path_two)
        merge_times += 1
    new_path = os.path.dirname(buf_path[0]) + '/log_sort.txt'
    os.rename(buf_path[0], new_path)
    return new_path


def __judge(filename):
    rf = open(filename, 'r')
    last = next(rf, None)
    while not last is None:
        now = next(rf, None)
        if now is None:
            break
        if now < last:
            print(last)
            print(now)
            return False
        last = now
    return True


if __name__ == "__main__":
    a = time.time()
    sort_big_file('/home/cao/桌面/江苏/20190528-J1242-x1-esr-suzhou/pcc/20190528181932_CC_range_5kmh/tmp.txt')
    ex = __judge('/home/cao/桌面/江苏/20190528-J1242-x1-esr-suzhou/pcc/20190528181932_CC_range_5kmh/t_log_sort.txt')
    print(ex, time.time() - a)