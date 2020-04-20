# filename: lan_ip_scan.py
import netifaces
import nmap


def get_gateways():
    return netifaces.gateways()['default'][netifaces.AF_INET][0]

def get_ip_lists(gateway):
    ip_lists = []
    for i in range(1, 256):
        ip_lists.append('{}{}'.format(gateway[:-1], i))
    return ip_lists

def scan_ip_survial(ip):
    nmScan = nmap.PortScanner()
    nmScan.scan(hosts=ip, arguments='-sP')
    if nmScan[ip]['hostnames'][0]['name']:
        return {'IP Address:': ip,
                'Hostname:': nmScan[ip]['hostnames'][0]['name']
               }
    else:
        return None

def get_all_survial_hosts():
    survial_hosts = []
    gateway = get_gateways()
    ip_lists = get_ip_lists(gateway)
    for ip in ip_lists:
        scan_rst = scan_ip_survial(ip)
        if scan_rst:
            survial_hosts.append(scan_rst)
            print(scan_rst)
    return survial_hosts


if __name__ == '__main__':
    get_all_survial_hosts()