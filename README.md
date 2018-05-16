# pc-viewer
pc-viewer是一个实时显示车道线，车辆，以及相关参数的工具。

## 依赖库
* cv2
* numpy

## 使用
1. 修改/etc/network/interfaces，设置电脑IP为静态地址与设备同一网段，例：

```shell
auto ens33(网卡名)
iface ens33 inet static
address 192.168.0.110
netmask 255.255.255.0
gateway 192.168.0.0
```
重启网络服务： /etc/init.d/networking restart

2. 运行pc-viewer

```shell
usage: run.py [-h] [--ip IP] [--origin ORIGIN] [--result RESULT] [--path PATH]

optional arguments:
  -h, --help       show this help message and exit
  --ip IP          ip address
  --origin ORIGIN  是否保存原始图片，1保存，0不保存，默认不保存
  --result RESULT  是否保存处理后图片，1保存，0不保存，默认不保存
  --path PATH      保存图片的路径，若保存图片必须指定该路径
```