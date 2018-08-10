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

* websockets
```shell
pip3 install websockets
```

## 使用
1. 修改/etc/network/interfaces，设置电脑IP为静态地址与设备同一网段，
例：

```shell
auto ens33(网卡名)
iface ens33 inet static
address 192.168.0.110
netmask 255.255.255.0
```
重启网络服务： /etc/init.d/networking restart

2. 配置pc-viewer

```shell
在etc/config.py可以配置运行的参数。
```

3. 运行pc-viewer

```shell
usage: python3 run_pcviewer.py
```

# 安装 pc-viewer
1. 安装应用图标

```shell
介绍：方便非研发人员使用，为pc-viewer制作启动图标和关闭图标，并锁定在左侧栏。
```
``` 步骤1：shell
将pc-viewer/assets/pcviewer.desktop 和 pc-viewer/assets/pcviewer-close.desktop 拷贝到/usr/share/applications/目录下。
```
```步骤2：
将上述两个文件内的路径指向pc-viewer所在路径。
```

2. 使用cython编译成可执行文件
```shell
介绍：给客户的电脑，需要将核心代码编译成.so文件。
```
```shell
步骤1：将client/和etc/目录下的xx.py文件后缀改为xx.pyx(setup.py不用改);
```
```shell
步骤2：将etc目录的definde.pyx 和 config.pyx 拷贝到client目录下。
```
```shell
步骤3：改变client/目录内引用自定义文件的方式，即import .draw.base改为include ”draw/base.pyx"
```
```shell
步骤4：执行build.sh，生成xxx.so文件。
```
```shell
步骤5：删除client目录下除步骤3生成的xxx.so文件。并删除etc目录
```
