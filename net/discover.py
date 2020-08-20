import socket
from threading import Thread, Event
from time import sleep
import json


class CollectorFinder(Thread):
    def __init__(self):
        super(CollectorFinder, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.found = {}
        self.exit = Event()
        # self.q = Queue()
        self.s.settimeout(0.2)
        # self.s.setblocking(0)

    def request(self):
        network = '192.168.98.255'
        try:
            self.s.sendto('Request MINIEYE'.encode('utf-8'), (network, 1060))
        except Exception as e:
            pass

    def run(self):
        try:
            self.s.bind(('0.0.0.0', 9010))
        except Exception as e:
            print('address for collector finder is already in use. exit.')
            return
        while not self.exit.isSet():
            try:
                ret = self.s.recvfrom(65536)
                data, address = ret
                # print('response from {}:{}'.format(address, data.decode('utf-8')))
                # self.q.put(ret)
                # print(data)
                if data[0] == 123:
                    data = json.loads(data.decode())
                self.found[address[0]] = data
                sleep(0.01)
            except socket.error as e:
                continue
        print('collector finder close.')
        self.s.detach()
        self.s.close()

    def find(self):
        return self.found

    def close(self):
        self.exit.set()


if __name__ == "__main__":
    import time
    finder = CollectorFinder()
    finder.start()
    for i in range(3):
        finder.request()
        sleep(1)

    # print(finder.found)
    finder.close()
    time.sleep(0.5)
    print("closed finder", finder.is_alive())
    finder = CollectorFinder()
    finder.start()
    while True:
        sleep(1)
