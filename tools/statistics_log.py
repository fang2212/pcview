import argparse
import logging
import os
from datetime import datetime
from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('--file', '-f', dest='files', action="append", help='log文件路径', required=True)
parser.add_argument('--debug', '-d', action='store_true', help='调试模式', default=False)
parser.add_argument('--save', '-s', help='保存统计图表文件夹路径（默认当前目录）', default='.')
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
    save_dir = '.'
    logging.warning(f"--save参数提供的路径不存在，改为根目录保存")

date_str = datetime.now().strftime("%Y%m%d%H%M%S")
save_dir = os.path.join(save_dir, date_str)
os.makedirs(save_dir)

process_show = 0

def main():
    # 对log文件参数进行统计
    for file in args.files:
        with open(file) as f:
            lines = f.readlines()

            can_map = {}  # can设备数据统计表
            for line in lines:
                if line == '':
                    continue

                # 格式化日志数据
                cols = line.strip().split(" ")
                if "CAN" in cols[2]:
                    data = {
                        "ts": float(cols[0]) + float(cols[1]) / 1000000,
                        "name": cols[2],
                        "id": cols[3]
                    }
                    # 更新CAN数据表
                    if not can_map.get(cols[2]):
                        logging.debug(f"设备：{cols[3]}")
                        can_map[cols[2]] = {}

                    # 更新CAN id表
                    if can_map[cols[2]].get(cols[3]):
                        can_map[cols[2]][cols[3]].append(data)
                    else:
                        can_map[cols[2]][cols[3]] = [data]

            # 统计
            statistics(can_map)


def statistics(can_map):
    """
    统计CAN数据接收情况
    """
    # 设置主图像素跟大小
    # plt.rcParams['figure.dpi'] = 300

    count = 10  # 每张图片限制显示10个 太多的话会导致无法正常显示
    for can in tqdm(can_map):
        # print("can:", can)
        logging.debug(f"statistics can:{can}")
        id_list = list(can_map[can].keys())
        img_num = 1
        for i in range(0, len(id_list), count):
            split_can_id = id_list[i: i+count]
            render_list = [can_map[can][can_id] for can_id in split_can_id]
            render(render_list, f"{can}_{img_num}")
            img_num += 1


def render(can, can_name):
    """渲染CAN设备的接收情况图表"""
    # 设置主图像素跟大小
    can_id_count = len(can)
    row_count = int(can_id_count / 2) + can_id_count % 2
    # print(f"count: {can_id_count}, row_count: {row_count}")
    plt.rcParams['figure.dpi'] = 200
    plt.rcParams['figure.figsize'] = 15, row_count * 5

    count = 0
    for can_id_data in can:
        # print(f"{can_id_data[0].get('id')} len:", len(can_id_data))
        if len(can_id_data) <= 1:
            continue

        count += 1
        # 渲染子图图表
        if count == can_id_count and can_id_count % 2 != 0:
            plt.subplot(row_count, 1, row_count)
        else:
            plt.subplot(row_count, 2, count)
        interval_list = []
        timestamp_list = []
        prev_timestamp = 0
        for data in can_id_data:
            timestamp_list.append(data.get("ts"))
            if not prev_timestamp:
                prev_timestamp = data.get("ts")
                continue

            # 计算接收间隔
            time_interval = data.get("ts") - prev_timestamp
            interval_list.append(time_interval)
            prev_timestamp = data.get("ts")

        # 求均值、最大值、最小值
        avg_interval = np.mean(interval_list)
        min_interval = np.min(interval_list)
        max_interval = np.max(interval_list)

        # 渲染
        plt.title(f"can id:{can_id_data[0].get('id')}")
        plt.xlabel("timestamp")
        plt.ylabel("interval(s)")
        avg_line = plt.axhline(y=avg_interval, color="r", linestyle="--", linewidth=1)
        min_line = plt.axhline(y=min_interval, color="g", linestyle="--", linewidth=1)
        max_line = plt.axhline(y=max_interval, color="y", linestyle="--", linewidth=1)
        plt.legend([avg_line, min_line, max_line], [f'avg:{"%.8f" % avg_interval}', f'min:{"%.8f" % min_interval}',
                                                    f'max:{"%.8f" % max_interval}'], bbox_to_anchor=(0, -0.23, 1, 2),
                   loc="lower left", mode="expand", borderaxespad=0, ncol=3)
        plt.scatter(timestamp_list[1:], interval_list, s=1, marker='.')  # s表示面积，marker表示图形

    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, hspace=0.1, wspace=0.1)
    plt.tight_layout()
    plt.suptitle(can_name, fontsize="xx-large")
    plt.savefig(f'{os.path.join(save_dir, can_name)}.png', dpi=200, format='png')
    plt.close()


if __name__ == "__main__":
    main()
