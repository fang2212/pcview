#!/usr/bin/env bash

if [ -d "dist" ]; then
  rm -r dist
fi
if [ -d "build" ]; then
  rm -r build
fi

python3 tools/build_info.py
pyinstaller pcc.spec
pyinstaller pcc_replay.spec
pyinstaller pcc_post.spec
cp /usr/local/lib/libnanomsg.so dist/pcc/libnanomsg.so
cp /usr/local/lib/libnanomsg.so.5 dist/pcc/libnanomsg.so.5
cp dist/log_manipulate/log_manipulate dist/pcc/
cp dist/pcc_replay/pcc_replay dist/pcc/
mv build_info.txt dist/pcc/
#mkdir dist/pcc/tk
#mkdir dist/pcc/tcl
rm dist/pcc/config/local.json

tar -czvf pcc.tar.gz dist/pcc

echo "removing build dirs..."
rm -r dist
rm -r build

echo "done."