import argparse
import logging
import os
import shutil
import time

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('--log', '-l', help='log文件路径', required=True)
parser.add_argument('--debug', '-d', action='store_true', help='调试模式', default=False)
parser.add_argument('--save', '-s', help='保存统计文件夹路径（默认当前目录）', default='.')
args = parser.parse_args()

# 初始化日志输出
log_level = "WARNING"
if args.debug:
    log_level = "DEBUG"
logging.basicConfig(format='%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S', level=log_level)

# 初始化保存路径
if os.path.exists(args.save):
    save_dir = args.save
else:
    save_dir = os.path.join(os.getcwd(), '.')
    logging.warning(f"--save参数提供的路径不存在，改为根目录保存")

# date_str = datetime.now().strftime("%Y%m%d%H%M%S")
save_dir = os.path.join(save_dir, "mark标记日志")
if os.path.exists(save_dir):
    shutil.rmtree(save_dir)
os.makedirs(save_dir)


def main():
    # 对log文件参数进行统计
    with open(args.log) as f:
        lines = f.readlines()

        marking = False
        mark_file = None
        for line in lines:
            if line == '':
                continue

            # 格式化日志数据
            cols = line.strip().split(" ")
            if "mark" in cols[2]:
                if "start" in cols[3]:
                    ts = float(cols[0]) + float(cols[1]) / 1000000
                    filename = time.strftime("%Y-%m-%d %H:%M:%S mark.txt", time.localtime(ts))
                    mark_file = open(os.path.join(save_dir, filename), 'w+')
                    marking = True
                    continue
                elif "end" in cols[3]:
                    marking = False
                    mark_file.flush()
                    mark_file.close()
                    continue

            if marking and mark_file:
                mark_file.write(line)

        # 防止未获取到结束标签
        if mark_file:
            mark_file.flush()
            mark_file.close()


if __name__ == "__main__":
    main()
