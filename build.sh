#!/bin/bash

mkdir dist/
./clear.sh
rm -r dist/*
mkdir -p dist/client/draw
mkdir -p dist/etc
cp run_pcview.py dist/
cp -r CANAlyst dist/
# cp -r etc dist/
cp -r assets dist/
cd client
pwd
python3 setup.py build_ext --inplace
cp *.so ../dist/client
# cp *.c ../dist/client
cp draw/*.so ../dist/client/draw
# cp draw/*.c ../dist/client/draw
# mv build ../dist/
# rm ../dist/client/*.c
# rm ../dist/client/draw/*.c
# rm -r ../dist/build
cd ..

cd etc
pwd
python3 setup.py build_ext --inplace
cp *.so ../dist/etc
cd ..