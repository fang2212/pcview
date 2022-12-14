import os
import threading
import functools
from multiprocessing.dummy import Process as Thread
import time
import psutil


class Supervisor(Thread):
    def __init__(self):
        super(Supervisor, self).__init__()
        # self.checkers = checkers
        self.checkers = []
        self.result = []
        self.exit = False

    def run(self):
        print('supervisor inited with {} tasks.'.format(len(self.checkers)))

        while not self.exit:
            self.result.clear()
            ts_now = time.time()
            wait_until = 1.0
            for checker in self.checkers:
                try:
                    if ts_now > checker['next_check']:
                        ret = checker['checker']()
                        if ret.get('status') != 'ok':
                            self.result.append(ret.get('info'))
                        checker['next_check'] = ts_now + checker['interval']
                        wait_until = min(wait_until, checker['interval'] + ts_now - time.time())
                except Exception as e:
                    pass
            if wait_until > 0.002:
                time.sleep(wait_until)
            self.check()

    def add_check_task(self, func, interval=1):  # interval in s
        self.checkers.append({'checker': func, 'interval': interval, 'next_check': 0})

    def check(self):
        return self.result

    def close(self):
        print("supervisor exit")
        self.exit = True


def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert, data))
    if isinstance(data, list):   return list(map(convert, data))
    if isinstance(data, set):    return set(map(convert, data))
    return data


def log_sort(log_path):
    """
    对log文件进行排序处理，并生成排序后的log_sort.txt
    """
    r_sort = os.path.join(os.path.dirname(log_path), 'log_sort.txt')

    if os.path.exists(r_sort):
        return r_sort
    else:
        return sort_big_file(log_path)


def sort_big_file(filename, file_splits=4, my_cmp=None):
    idx = 0
    buf_file = []
    buf_path = []
    path = os.path.dirname(filename)
    with open(filename, 'r', encoding='unicode_escape') as rf:
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


def check_cpu_time():
    return psutil.cpu_percent(interval=20, percpu=False)


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