#!/bin/bash

./build.sh

cp kill.sh pc-viewer.sh pc-viewer-color.sh dist/
cp install_dependencies.sh /home/minieye/env/env/ 
cp -r dist ~/env/