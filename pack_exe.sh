#!/usr/bin/env bash
# 如果用虚拟环境，必须在venv下进行
#if [ -d "dist" ]; then
#  rm -r dist
#fi
if [ -d "build" ]; then
  rm -r build
fi

#python3 tools/build_info.py
pyinstaller -F pcc_app_yj.spec
pyinstaller -F pcc_replay_yj.spec
#pyinstaller pcc_post.spec

if [ -d "dist/pcc_release" ]; then
	rm -rf ./dist/pcc_release/*
	echo "remove!!..."  	
else
  	mkdir ./dist/pcc_release
	echo "mkdir!!..."
fi


mv dist/pcc_app dist/pcc_release/
mv dist/pcc_replay dist/pcc_release/
#mv build_info.txt dist/pcc_release/
cp -r config dist/pcc_release/
cp -r dbc dist/pcc_release/
#mkdir dist/pcc/tk
#mkdir dist/pcc/tcl
rm dist/pcc/config/local.json

cd dist
tar -czvf pcc_release.tar.gz pcc_release

echo "removing build dirs..."
#rm -r dist
#rm -r build

echo "done."
