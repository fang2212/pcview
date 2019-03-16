:
:npm install pkg --global
:python3 -m pip install pyinstaller

echo "clear"
del *.spec
rd/s/q release\win\build
rd/s/q release\win\dist

echo "start pyinstaller"
pyinstaller flow_view.py --distpath release\win\dist --workpath release\win\build

echo "copy *.node"
copy release\lib\win\msgpackBinding.node release\win\dist
copy release\lib\win\opencv_ffmpeg330_64.dll release\win\dist\flow_view
copy node\msg_fd.exe release\win\dist
copy node\status2log.exe release\win\dist