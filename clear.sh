#!/bin/bash

cd client
pwd
rm *.so
rm *.c
rm draw/*.so
rm draw/*.c
rm -r build
cd ..
cd etc
rm *.so
rm *.c
rm -r build
cd ..