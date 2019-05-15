import netifaces, nmap
import nanomsg
from nanomsg import Socket, PAIR, PUB, SUB


def get_gateways():
    return netifaces.gateways()['default'][netifaces.AF_INET][0]


def get_ip_lists(ip):
    ip_lists = []
    for i in range(1, 256):
        ip_lists.append('{}{}'.format(ip[:-1], i))
    return ip_lists


def main(ip=None):
    ip = get_gateways()
    ip_lists = get_ip_lists(ip)
    nmScan, temp_ip_lists, hosts = nmap.PortScanner(), [], ip[:-1] + '0/24'
    # print(hosts)
    # for addr in ip_lists:
    #     ret = nmScan.scan(hosts=addr, arguments='-p')
    #     print(ret)
    # print(nmScan.all_hosts())
    # print(nmScan.csv())
    results = nmScan.scan(hosts='192.168.98.227', ports='1208, 1209', arguments='-T4 -A -v -Pn ')
    print(results)
    ret = nmScan.scan(hosts=hosts, arguments='-sP')
    print(ret)
    # print('扫描时间：' + ret['nmap']['scanstats']['timestr'] + '\n命令参数:' + ret['nmap']['command_line'])
    # for ip in ip_lists:
    #     print('ip地址：' + ip + '：')
    #     if ip not in ret['scan']:
    #         temp_ip_lists.append(ip)
    #         print('扫描超时')
    #     else:
    #         print('已扫描到主机，主机名：' + ret['scan'][ip]['hostnames'][0]['name'])
    # print(str(hosts) + ' 网络中的存活主机:')
    # for ip in temp_ip_lists: ip_lists.remove(ip)
    # for ip in ip_lists: print(ip)


def search_hosts():
    local = get_gateways()
    ip_lists = get_ip_lists(local)
    nm = nmap.PortScanner()
    field = local[:-1] + '0/24'
    ret = nm.scan(hosts=field, arguments='-sP')
    print(len(ret['scan']))
    for ip in ip_lists:
        if ip in ret['scan']:
            # socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
            socket = Socket(SUB)
            # nanomsg.wrapper.nn_setsockopt(socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
            # nanomsg.wrapper.nn_connect(socket, "tcp://%s:%s" % (ip, 1200,))
            socket.connect("tcp://%s:%s" % (ip, 1200,))
            recv = nanomsg.wrapper.nn_recv(socket, 0.01)
            if len(recv) > 0:
                print("a host found:", ip)

if __name__ == '__main__':
    # main()
    # print(get_ip_lists(get_gateways()))
    search_hosts()
