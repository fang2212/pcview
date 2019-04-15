:: 
:: npm install pkg --global
:: python3 -m pip install pyinstaller

echo "clear"
del *.spec
rd/s/q release\win\build
rd/s/q release\win\dist

echo "start pyinstaller"
pyinstaller xilinx_view.py --distpath release\win\dist --workpath release\win\build

echo "copy *.node"
echo "make sure copy msgpackBinding.node from node to release\win\ " 
echo "make sure copy opencv-ffmpeg*.dll from PYTHON_PATH\Lib\site-packages\cv2to release\win\ "
copy release\win\msgpackBinding.node release\win\dist\xilinx_view
copy release\win\opencv_ffmpeg*.dll release\win\dist\xilinx_view

copy node\msg_fd.exe release\win\dist\xilinx_view
copy node\status2log.exe release\win\dist\xilinx_view
copy docs\releaseGuide.md release\win\dist\xilinx_view