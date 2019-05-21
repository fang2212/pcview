import socket
from multiprocessing.dummy import Process
from time import sleep
import json


class CollectorFinder(Process):
    def __init__(self):
        Process.__init__(self)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind(('0.0.0.0', 9010))
        self.found = {}
        # self.q = Queue()
        # self.s.settimeout(0.2)
        # self.s.setblocking(0)

    def request(self):
        network = '192.168.98.255'
        try:
            self.s.sendto('Request MINIEYE'.encode('utf-8'), (network, 1060))
        except Exception as e:
            pass

    def run(self):
        while True:
            try:
                ret = self.s.recvfrom(65536)
                data, address = ret
                # print('response from {}:{}'.format(address, data.decode('utf-8')))
                # self.q.put(ret)
                # print(data[0])
                if data[0] == 123:
                    data = json.loads(data.decode())
                self.found[address[0]] = data
                sleep(0.01)
            except socket.error as e:
                print(e)

    def find(self):
        return self.found


if __name__ == "__main__":
    finder = ColletorFinder()
    finder.start()
    for i in range(3):
        finder.request()
        sleep(0.2)

    print(finder.found)

    while True:
        sleep(1)
