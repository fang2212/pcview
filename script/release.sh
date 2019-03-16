#!/bin/bash

rm -r release
mkdir release
cp flow_view.py release/
cp -r sink release/
cp -r recorder release/
cp -r player release/
cd release
rm -r player/__pycache__
rm -r recorder/__pycache__
rm -r sink/__pycache__