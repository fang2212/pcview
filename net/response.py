import socket
import netifaces
import uuid


def get_mac_address():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

PORT = 1060

s.bind(('0.0.0.0', PORT))
print('Listening for broadcast at ', s.getsockname())

def get_gateways():
    return netifaces.gateways()['default'][netifaces.AF_INET][0]

while True:
    data, address = s.recvfrom(65535)
    print('Server received from {}:{}'.format(address, data.decode('utf-8')))

    s.sendto('my MAC is {}'.format(get_mac_address()).encode('utf-8'),(address[0], 9010))