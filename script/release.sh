#!/bin/bash

cp flow_view.py release/pcview
cp -r sink release/pcview
cp -r recorder release/pcview
cp -r player release/pcview
cd release/pcview
rm -r player/__pycache__
rm -r recorder/__pycache__
rm -r sink/__pycache__