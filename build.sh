#!/bin/bash

# 初始化dist目录
mkdir dist/
./clear.sh
rm -r dist/*
mkdir -p dist/client
mkdir -p dist/etc
# 把 run_pcview.py CANAlyst/ assets/ 复制到dist目录下
cp run_pcview.py dist/
cp -r CANAlyst dist/
cp -r assets dist
# 把client目录下的.py文件编译成.so文件，并复制到 dist/client/ 目录下
cd client
python3 setup.py build_ext --inplace
cp *.so ../dist/client
cd ..
# 把etc目录下的.py文件编译成.so文件，并复制到 dist/etc/ 目录下
cd etc
python3 setup.py build_ext --inplace
cp *.so ../dist/etc
cd ..