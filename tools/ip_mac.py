# import nmap
import os


def print_ip_mac(ip_mac):
    print('------- LAN devices found -------')
    for mac in ip_mac:
        print(mac, ip_mac[mac])


def nmap_scan(ip_range='192.168.98.0/24', async=True):
    r = os.popen('nmap -T5 -sP {}'.format(ip_range))
    if async:
        return
    for line in r:
        # print(line, end='')
        pass
    r.close()


def get_macs(ip_range='192.168.98.0/24'):
    ip = ip_range.split('/')[0].split('.')
    ip_kw = '.'.join(ip[:3])
    mac_ip = dict()
    with open('/proc/net/arp') as arp:
        for line in arp:
            fields = list(filter(None, line.split(' ')))
            mac = fields[3]
            ip = fields[0]
            # print(mac, ip)
            if ip_kw in ip:
                mac_ip[mac] = ip

    print_ip_mac(mac_ip)
    return mac_ip


def get_mac_ip(ip_range='192.168.98.0/24'):
    nmap_scan(ip_range, async=True)
    mac_ip = get_macs(ip_range)
    return mac_ip


if __name__ == "__main__":
    nm = get_mac_ip()
    # while nm.still_scanning():
    #     print('scanning...')
    #     nm.wait(2)
