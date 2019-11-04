import socket


def detect_network(ipaddr='www.baidu.com', port=80):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ipaddr, port))
        # print('ok')
        return True
    except socket.error as e:
        # print('offline')
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    detect_network('www.baidu.com', 80)
