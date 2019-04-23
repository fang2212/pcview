#!/bin/bash
echo "clear"
rm *.spec
rm -r release/linux/build
rm -r release/linux/dist

echo "start pyinstaller"
rm release/linux/dist/flow_view
pyinstaller flow_view.py -F --distpath release/linux/dist --workpath release/linux/build

echo "copy *.node"
cp release/linux/msgpackBinding.node release/linux/dist
cp node/msg_fd release/linux/dist
cp node/status2log release/linux/dist
cp docs/releaseGuide.md release/linux/dist
cp -r dbc/ release/linux/dist/dbc/