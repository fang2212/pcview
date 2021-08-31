import socket
from threading import Thread, Event
from time import sleep
import json
import nmap

from utils import logger


class CollectorFinder(Thread):
    """
    采集器扫描线程，从当前局域网中匹配在线的采集设备
    """
    def __init__(self, network='192.168.98.0/24'):
        super(CollectorFinder, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.network = network
        self.found = {}
        self.exit = Event()
        self.s.settimeout(0.2)

    def run(self):
        try:
            self.s.bind(('0.0.0.0', 9010))
        except Exception as e:
            print('address for collector finder is already in use. exit.')
            return

        # 循环更新在线设备
        while not self.exit.is_set():
            try:
                ret = self.s.recvfrom(65536)
                data, address = ret
                if data[0] == 123:
                    data = json.loads(data.decode())
                ip = address[0]
                if ip not in self.found:
                    print('found new device:', ip, data)
                self.found[address[0]] = data
            except socket.error as e:
                continue
            sleep(0.2)

        logger.warning('collector finder close.')
        self.s.detach()
        self.s.close()

    def take_request(self):
        """
        请求在线设备
        :return:
        """
        seg = self.network.split('.')
        broadcast = '.'.join(seg[:3]) + '.255'
        try:
            self.s.sendto('Request MINIEYE'.encode('utf-8'), (broadcast, 1060))
        except Exception as e:
            logger.error("finder request err: {}".format(e))

        # 扫描在线ip
        self.nmap_scan()
        # 获取ip对应的mac地址
        macs = self.get_macs()
        for mac in macs:
            if mac.startswith('5a:31') or mac.startswith("6a:92"):
                ip = macs[mac]
                if ip not in self.found:
                    print('nmap found new device:', ip, mac)
                    self.found[ip] = {'mac': mac}

    def nmap_scan(self):
        """
        通过nmap来扫描局域网内的在线ip
        :return:
        """
        ips = []
        nm = nmap.PortScanner()
        nm.scan(hosts=self.network, arguments='-sP -T5')
        for t in nm.all_hosts():
            ips.append(nm[t]['addresses']['ipv4'])

        return ips

    def load_cached_macs(self, cached_macs):
        """
        从缓存文件中加载mac
        :param cached_macs:
        :return:
        """
        for mac in cached_macs:
            if mac.startswith('5a:31') or mac.startswith("6a:92"):
                ip = cached_macs[mac]
                if ip not in self.found:
                    self.found[ip] = {'mac': mac}

    def get_macs(self):
        """
        通过linux系统的arp文件获取ip对应的mac
        :return:
        """
        ip = self.network.split('/')[0].split('.')
        ip_kw = '.'.join(ip[:3])
        mac_ip = dict()
        with open('/proc/net/arp') as arp:
            for line in arp:
                fields = list(filter(None, line.split(' ')))
                mac = fields[3]
                ip = fields[0].strip()
                ip_prefix = '.'.join(ip.split('.')[:3])
                if ip_prefix == ip_kw:
                    mac_ip[mac] = ip
        return mac_ip

    def find(self):
        return self.found

    def close(self):
        self.exit.set()


if __name__ == "__main__":
    finder = CollectorFinder()
    finder.start()
    for i in range(3):
        finder.take_request()
        sleep(1)

    print("found:", finder.found)
    finder.close()
    print("closed finder", finder.is_alive())
