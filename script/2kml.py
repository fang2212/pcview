import simplekml
import argparse
import os
import shutil

"""
1 pip install simplekml
2 python /home/minieye/桌面/2kml.py --filepath /home/minieye/桌面/1/1/20201027113623/log.txt --color 1 --width 3
3 .kml保存在.log同级目录   
"""

def to_kml(filepath, kmlname, savepath, color=0, width=3):
    kml = simplekml.Kml()
    lists = []
    lists2 = []
    lists3 = []

    with open(filepath, 'r') as f:
        for line in f.readlines():
            list =line.split(' ')
            if list[2] == 'tcp.5.inspva':
                lists.append(list[3])
    for i in range(len(lists)):
        list = lists[i].split(',')
        lists2.append(list)
    for i in range(len(lists2)):
        listt = lists2[i][12:10:-1]      #[12, 10)
        listt.append(lists2[i][13])
        lists3.append(listt)
    print(lists3)

    lin = kml.newlinestring(name='Pathway', description='A path way', coords=lists3)          #添加轨迹

    if color == 0:
        lin.style.linestyle.color = simplekml.Color.red
    if color == 1:
        lin.style.linestyle.color = simplekml.Color.green
    if color == 2:
        lin.style.linestyle.color = simplekml.Color.blue
    lin.style.linestyle.width = width
    kml.save(kmlname)

    shutil.move(kmlname, savepath)
    return kml

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath', help='log file path')
    parser.add_argument('--color', default=0, help='color of line;   0:red 1:green 2:blue', type=int)
    parser.add_argument('--width', default=3, help='the width of line', type=int)
    args = parser.parse_args()

    filepath = args.filepath
    color = args.color
    width = args.width

    # filename = os.path.basename(filepath)
    filename = os.path.dirname(filepath)
    kmlname = filename.split('/')[-1] + '.kml'
    savepath = os.path.abspath(os.path.join(filepath, '../')) + '/'


    kml = to_kml(filepath, kmlname, savepath, color=color, width=width)
    print(kml.kml())
