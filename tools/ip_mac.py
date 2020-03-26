# import nmap
import os
import subprocess
import json
import time


def print_ip_mac(ip_mac):
    print('------- LAN devices found -------')
    for mac in ip_mac:
        print(mac, ip_mac[mac])


def ping(ip):
    r = os.popen('ping -c 1 -W 500 -i 0.2 {}'.format(ip))
    for line in r:
        # print(line)
        pass


def nmap_scan(ip_range='192.168.98.0/24', isasync=False):
    p = subprocess.Popen(['nmap', '-T5', '-sP', '{}'.format(ip_range)], stdout=subprocess.PIPE)
    stdout = p.stdout
    # print(stdout)
    ips = []
    if isasync:
        return
    for bline in stdout:
        line = bline.decode()
        # print(line, end='')
        if 'Nmap scan report for' in line:
            ip = line.split(' ')[4]
            ips.append(ip)
        pass
    # r.close()
    return ips


def get_macs(ip_range='192.168.98.0/24'):
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

    print_ip_mac(mac_ip)
    return mac_ip


def get_cached_macs(cfg_name, cachefile='config/runtime/cached_macs.json', timeout=600):
    if not os.path.exists(cachefile):
        return
    cached = json.load(open(cachefile))
    if cfg_name not in cached:
        return
    if time.time() - cached[cfg_name]['ts'] > timeout:
        print('mac table timed out.')
        return
    # print_ip_mac(cached[cfg_name]['data'])
    return cached[cfg_name]['data']


def save_macs(cfg_name, mac_ip, cachefile='config/runtime/cached_macs.json'):
    if not os.path.exists(cachefile):
        to_save = {cfg_name: {'ts': time.time(), 'data': mac_ip}}
        json.dump(to_save, open(cachefile, 'w'), indent=True)
    else:
        saved = json.load(open(cachefile))
        saved[cfg_name] = {'ts': time.time(), 'data': mac_ip}
        json.dump(saved, open(cachefile, 'w'), indent=True)
        

def get_mac_ip(ip_range='192.168.98.0/24', isasync=False):
    ips = nmap_scan(ip_range, isasync=isasync)
    if not ips:
        print('nmap found no device in {}.'.format(ip_range))
        return
    for ip in ips:
        ping(ip)
    mac_ip = get_macs(ip_range)
    return mac_ip


if __name__ == "__main__":
    nm = get_mac_ip()
    print(nm)
    # while nm.still_scanning():
    #     print('scanning...')
    #     nm.wait(2)
