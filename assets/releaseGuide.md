## 日志记录
```shell
./status2log
# or
./status2log --event-log # timelog 及 eventlog都存储
# 选项说明
# --ip xxx.xxx.xxx.xxx # 默认192.168.0.233
# --log-path xxx/xxx/xxx #log存储路径地址,默认./rotor_data
# --event-log # 存储事件日志,默认不存储
# --print # 命名行打印输出,默认不打印
```

## pcview
```shell
# msg_fd.js转发程序只需要启动一次，不被kill掉就一直能执行转发服务
./msg_fd #默认ip 192.168.0.233 
# or
./msg_fd 127.0.0.1 #linux 流图时监听本地ip
# flow_view --help 查看选项
./flow_view # 默认在同级目录pcview_data下存储日志及视频
```
## 更新记录
* 20190316
1. 添加车道线报警信息
1. 添加frame_id及时间
1. 行人回归框关键行人粉红色其他绿色
1. 添加车辆类型
1. 从libflow接收到的信息中是字典的添加frame_id字段 