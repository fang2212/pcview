
#使用串口can时，修改usb权限
sudo cat>/etc/udev/rules.d/70-ttyusb.rules<<EOF
KERNEL=="ttyUSB[0-9]*", MODE="0666"
EOF