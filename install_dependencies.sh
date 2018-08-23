#!/bin/bash

# Install dependencies
sudo apt-get -y update
sudo apt install -y vim
sudo apt install -y usbrelay
sudo apt install -y fish
sudo apt install -y tmux
sudo apt install -y htop
sudo apt install -y zip
sudo apt install -y openssh-server
sudo apt install -y screen 
sudo apt-get install -y wget
sudo apt-get install -y build-essential pkg-config cmake git
sudo apt-get install -y libjpeg-dev libjasper-dev libpng-dev libtiff-dev libwebp-dev
sudo apt-get install -y libavcodec-dev libavformat-dev libavresample-dev libavutil-dev libswscale-dev libv4l-dev libxine-dev
sudo apt-get install -y libgtk2.0-dev
sudo apt-get install -y libgphoto2-dev
sudo apt-get install -y libgl1-mesa-dev libglu1-mesa-dev libgles2-mesa-dev
sudo apt-get install -y python-dev python-numpy python3-dev python3-numpy
sudo apt-get install -y default-jre
sudo apt-get install -y gpsd libgps-dev libdc1394-22-dev libusb-1.0-0-dev
sudo apt-get install -y libtbb2 libtbb-dev
sudo apt-get install -y libatlas-base-dev gfortran
sudo apt-get install -y openexr
sudo apt-get install -y libavdevice-dev libavfilter-dev
sudo apt-get install -y gcc-multilib
sudo apt-get install -y libgl1-mesa-dev libglu1-mesa-dev libgles2-mesa-dev
sudo apt-get install -y libjpeg-dev libjasper-dev libpng-dev libtiff-dev libwebp-dev


# This scripts installs OpenCV 3.1.0 into Ubuntu 14.04. (Also tested on Ubuntu 16.04)
# Refer to: http://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html

OpenCVDir="/home/minieye/env/opencv-3.1.0"

cd "$OpenCVDir"

mkdir -p build
cd build

cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D WITH_1394=NO \
      -D WITH_VTK=NO \
      -D WITH_CUDA=NO \
      -D WITH_EIGEN=NO \
      -D WITH_GSTREAMER=NO \
      -D WITH_GTK=YES \
      -D WITH_GTK_2_X=YES \
      -D WITH_JPEG=YES \
      -D WITH_PNG=YES \
      -D WITH_WEBP=YES \
      -D WITH_OPENEXR=NO \
      -D WITH_QT=NO \
      -D WITH_QUICKTIME=NO \
      -D WITH_V4L=YES \
      -D WITH_XINE=NO \
      -D WITH_GDAL=NO \
      -D WITH_GPHOTO2=YES \
      -D PYTHON2_EXECUTABLE=/usr/bin/python2.7 \
      -D PYTHON2_LIBRARIES=/usr/lib/x86_64-linux-gnu/libpython2.7.so \
      -D PYTHON2_INCLUDE_DIR=/usr/include/python2.7 \
      -D PYTHON2_INCLUDE_PATH=/usr/include/python2.7 \
      -D PYTHON2_NUMPY_INCLUDE_DIRS=/usr/lib/python2.7/dist-packages/numpy/core/include \
      -D PYTHON3_EXECUTABLE=/usr/bin/python3 \
      -D PYTHON3_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.5m.so \
      -D PYTHON3_LIBRARIES=/usr/lib/x86_64-linux-gnu/libpython3.5m.so \
      -D PYTHON3_INCLUDE_DIR=/usr/include/python3.5m \
      -D PYTHON3_INCLUDE_PATH=/usr/include/python3.5m \
      -D PYTHON3_NUMPY_INCLUDE_DIRS=/usr/lib/python3/dist-packages/numpy/core/include \
      -D BUILD_opencv_python2=YES \
      -D BUILD_opencv_python3=YES \
      -D BUILD_DOCS=NO \
      -D BUILD_TESTS=NO \
      -D BUILD_PERF_TESTS=NO \
      -D BUILD_EXAMPLES=YES \
      -D INSTALL_C_EXAMPLES=NO \
      -D INSTALL_PYTHON_EXAMPLES=NO \
      ..
      
make -j $(nproc)

# Install OpenCV
sudo make install

sudo /bin/bash -c 'echo "/usr/local/lib" > /etc/ld.so.conf.d/opencv.conf'
sudo ldconfig

echo "OpenCV has been successfully installed."

NanomsgDir="/home/minieye/env/nanomsg-1.1.3"

cd "$NanomsgDir"

mkdir build
cd build
cmake ..
cmake --build .
ctest .
sudo cmake --build . --target install
sudo ldconfig

sudo apt install -y python3-pip
sudo pip3 install nanomsg
sudo pip3 install msgpack
sudo pip3 install websockets
sudo pip3 install absl-py
echo "nanomsg msgpack has been successfully installed."

#PyAVDir="/home/minieye/env/PyAV"
#cd "$PyAVDir"
#python3 setup.py install
#echo "PyAV has been successfully installed."

DistDir="/home/minieye/env/dist/assets"
cd "$DistDir"
chomd a+x *.desktop
cp *.desktop /home/minieye/桌面/