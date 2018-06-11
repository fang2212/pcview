# pc-viewer
pc-viewer是一个实时显示车道线，车辆，以及相关参数的工具。

## 依赖库
* cv2
```shell
pip3 install opencv-python
```

* numpy
```shell
pip3 install numpy

```
* nanomsg
```shell
1. 下载源码https://github.com/nanomsg/nanomsg
    接着按下面操作
    % mkdir build
    % cd build
    % cmake ..
    % cmake --build .
    % ctest .
    % sudo cmake --build . --target install
    % sudo ldconfig (if on Linux)

2. sudo pip3 install nanomsg
```

* msgpack
```shell
pip3 install msgpack
```

## 使用
1. 修改/etc/network/interfaces，设置电脑IP为静态地址与设备同一网段，
例：

```shell
auto ens33(网卡名)
iface ens33 inet static
address 192.168.0.110
netmask 255.255.255.0
gateway 192.168.0.1
```
重启网络服务： /etc/init.d/networking restart

2. 运行pc-viewer

```shell
usage: python3 run_pcviewer.py [-h] [--ip IP] [--video VIDEO] [--alert ALERT] [--log LOG] [--path PATH]

  可选         参数     说明
  -h, --help           help
  --ip         IP      设备ip地址
  --video    VIDEO   是否保存视频，1保存，0不保存，默认不保存
  --alert    ALERT   是否保存警报信息和图片，用于演示平台，1保存，0不保存，默认不保存
  --log    LOG   是否保存日志，1保存，0不保存，默认不保存
  --path      PATH    保存路径
  
  实例：
  python3 run_viewer.py --ip 192.168.0.233 --video 1 --alert 0 --log 0 --path '/home/minieye/pc-viewer-data/'
```
