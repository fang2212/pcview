#!/usr/bin/env bash
# 如果用虚拟环境，必须在venv下进行
#if [ -d "dist" ]; then
#  rm -r dist
#fi
if [ -d "build" ]; then
  rm -r build
fi

#python3 tools/build_info.py
pyinstaller pcc_app.spec --noconfirm
pyinstaller pcc_replay.spec --noconfirm
pyinstaller split_recorder_data.spec --noconfirm
pyinstaller statistics_log.spec --noconfirm
#pyinstaller -F pcc_replay_yj.spec
#pyinstaller pcc_post.spec
#
#if [ -d "dist/pcc_release" ]; then
#	rm -rf ./dist/pcc_release/*
#	echo "remove!!..."
#else
#  	mkdir ./dist/pcc_release
#	echo "mkdir!!..."
#fi


#mv dist/pcc dist/pcc_release/
#mv dist/pcc_replay dist/pcc_release/
#mv build_info.txt dist/pcc_release/
#cp -r config dist/pcc_app/
#cp -r dbc dist/pcc_app/
#cp -r static dist/pcc_app/
#cp -r templates dist/pcc_release/
#mkdir dist/pcc/tk
#mkdir dist/pcc/tcl
rm dist/pcc_app/config/local.json
python3 tools/build_info.py
mv build_info.txt dist/pcc_app/

cd dist
cp pcc_replay/pcc_replay pcc_app/
cp split_recorder_data/split_recorder_data pcc_app/
cp statistics_log/statistics_log -r pcc_app/
cp -r pcc_app "pcc_app_"`date +%Y_%m_%d`
tar -czvf "pcc_app_"`date +%Y_%m_%d`.tar.gz "pcc_app_"`date +%Y_%m_%d`

#if [ ! -d "~/release " ]; then
#  mkdir ~/release
#fi

rm -rf "pcc_app_"`date +%Y_%m_%d`
#cp pcc_app.tar.gz ~/release/"PCC_APP_$(date "+%Y%m%d%H%M%S").tar.gz"

echo "removing build dirs..."
#rm -r dist
#rm -r build

echo "done."
