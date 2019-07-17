#!/bin/bash
echo "clear"
rm *.spec
rm -r release/linux/build
rm -r release/linux/dist

echo "start pyinstaller"
pyinstaller pcc.py -F --distpath release/linux/dist --workpath release/linux/build

echo "copy config"
mkdir release/linux/dist/config
cp -r config/*.json release/linux/dist/config/
cp -r config/collectors/ release/linux/dist/config

echo "copy dbc"
cp -r dbc/ release/linux/dist

echo "copy web"
cp -r web/ release/linux/dist/
