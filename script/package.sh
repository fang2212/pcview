#!/bin/bash
echo "clear"
rm *.spec
rm -r release/linux/build
rm -r release/linux/dist

echo "start pyinstaller"
rm release/linux/dist/flow_view
pyinstaller flow_view.py -F --distpath release/linux/dist --workpath release/linux/build

echo "copy *.node"
cp release/lib/linux/msgpackBinding.node release/linux/dist
cp node/v2/msg_fd release/linux/dist
cp node/v2/status2log release/linux/dist
cp docs/releaseGuide.md release/linux/dist