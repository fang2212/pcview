# 演示平台
DemoPlayer是一个ADAS演示平台，同时播放处理前的视频和处理后的视频，并配合m3警报。

## 依赖
* cv2
```shell
pip3 install opencv-python
```

* screeninfo
```shell
pip3 install screeninfo
```

## 使用
```shell
python3 run.py --path [data_path]
```
data_path包含origin目录，result目录以及demo.json，其中origin目录包含未处理的图片，result目录包含已经处理的图片，demo.json包含警报信息。origin，result，demo.json可以通过pc-viewer运行获得。
