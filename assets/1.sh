#!/bin/bash  
cd /home/minieye/env/frp
while [ '' == '' ]  
do  
ssh_d_process_num=`ps aux|grep -E 'frpc.ini' |grep -v grep |wc -l`  
if [ "$ssh_d_process_num" == "0" ]; then  
  ./frpc -c ./frpc.ini &  
fi  
sleep 30  
done  
