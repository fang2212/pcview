#!/bin/bash

./build.sh

cp kill.sh pc-viewer.sh pc-viewer-unsave.sh dist/
cp -r dist ~/env/