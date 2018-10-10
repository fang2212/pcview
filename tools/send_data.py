from nanomsg import Socket, PUB 
import time 
import json
import msgpack

#img_dir_path = "/media/minieye/data2/origin/"
#log_file_path = "/media/minieye/data2/log.json"

img_dir_path = "/media/zzp/tempdisk1/pcshow0824/origin/"
log_file_path = "/media/zzp/tempdisk1/pcshow0824/log.json"

if __name__ == "__main__":

    # 创建连接，5个端口
    send_lane = Socket(PUB)
    send_lane.bind("tcp://127.0.0.1:1203")
    send_vehicle = Socket(PUB)
    send_vehicle.bind("tcp://127.0.0.1:1204")
    send_ped = Socket(PUB)
    send_ped.bind("tcp://127.0.0.1:1205")
    send_tsr = Socket(PUB)
    send_tsr.bind("tcp://127.0.0.1:1206")
    send_pic = Socket(PUB)
    send_pic.bind("tcp://127.0.0.1:1200")

    #log 与 frame_id
    log_file = open(log_file_path)
    log_data = log_file.readlines()
    frame_id = -1

    # 照片前24位
    pre = lambda frame: b'0123' + frame + b'8901234567891234'

    send_set = set()
    for data in log_data:
        data = json.loads(data)
        for key in data:
            # 判断log发到哪个端口
            if key == 'lane':
                send_lane.send(msgpack.packb(data[key]))
            if key == 'vehicle':
                send_vehicle.send(msgpack.packb(data[key]))
            if key == 'ped':
                send_ped.send(msgpack.packb(data[key]))
            if key == 'tsr':
                send_tsr.send(msgpack.packb(data[key]))
            
            # 判断frame
            if 'frame_id' in data[key]:
                if frame_id < data[key]['frame_id']:
                    frame_id = data[key]['frame_id']
                    if frame_id not in send_set:
                        send_set.add(frame_id)
                        
                        try:
                            img_file = open(img_dir_path + str(frame_id) + '.jpg', 'rb')
                            print('img_file', img_file)
                            img_data = img_file.read()
                            send_pic.send(pre((frame_id).to_bytes(4, byteorder='little')) + img_data)
                        except:
                            print("wrong")

        time.sleep(0.01) 
