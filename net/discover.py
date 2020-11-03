import socket
from threading import Thread, Event
from time import sleep
import json
import nmap


class CollectorFinder(Thread):
    def __init__(self, network='192.168.98.0/24', configs=None):
        super(CollectorFinder, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.network = network
        self.found = {}
        self.exit = Event()
        # self.q = Queue()
        self.s.settimeout(0.2)
        # self.s.setblocking(0)

    def request(self):
        seg = self.network.split('.')
        broadcast = '.'.join(seg[:3]) + '.255'
        try:
            self.s.sendto('Request MINIEYE'.encode('utf-8'), (broadcast, 1060))
        except Exception as e:
            pass

        self.nmap_scan()
        # print('nmap scanned.')
        macs = self.get_macs()
        # print('mac table:', macs)
        for mac in macs:
            if mac.startswith('5a:31'):
                ip = macs[mac]
                if ip not in self.found:
                    print('nmap found new device:', ip, mac)
                    self.found[ip] = {'mac': mac}
                    yield ip, mac

    def nmap_scan(self):
        ips = []
        nm = nmap.PortScanner()
        nm.scan(hosts=self.network, arguments='-sP -T5')
        for t in nm.all_hosts():
            # print(nm[t])
            ips.append(nm[t]['addresses']['ipv4'])

        return ips

    def load_cached_macs(self, cached_macs):
        for mac in cached_macs:
            if mac.startswith('5a:31'):
                ip = cached_macs[mac]
                if ip not in self.found:
                    self.found[ip] = {'mac': mac}

    def get_macs(self):
        ip_range = self.network or '192.168.98.0/24'
        ip = ip_range.split('/')[0].split('.')
        ip_kw = '.'.join(ip[:3])
        mac_ip = dict()
        with open('/proc/net/arp') as arp:
            for line in arp:
                fields = list(filter(None, line.split(' ')))
                mac = fields[3]
                ip = fields[0].strip()
                # print(mac, ip)
                if ip_kw in ip:
                    mac_ip[mac] = ip

        # print('------- LAN devices found in arp -------')
        # for mac in mac_ip:
        #     print(mac, mac_ip[mac])
        return mac_ip

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
                # print('hahahahahaha')
                if data[0] == 123:
                    data = json.loads(data.decode())
                ip = address[0]
                if ip not in self.found:
                    print('found new device:', ip, data)
                self.found[address[0]] = data
                sleep(0.2)
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
