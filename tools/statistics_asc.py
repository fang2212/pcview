import argparse
import logging
import math
import os
import shutil
import time
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

other_list = ['gsensor', "camera"]     # 参与统计的其他字段

row_count = 3
col_count = 4


class Statistics:

    def __init__(self, log_path, save_path=None):
        self.log_path = log_path
        self.save_path = save_path
        self.file_name = os.path.split(log_path)[-1].split(".")[0] + '.png'
        # self.pool = Pool(4)                         # 初始化进程池

        self.record_data = []                           # 日志数据

        self.init()

    def init(self):
        if not (self.save_path and os.path.exists(self.save_path) and os.path.isdir(self.save_path)):
            self.save_path = os.path.join(os.path.dirname(self.log_path), "asc信号接收统计图表")
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

    def run(self):
        print("start:", self.log_path)
        with open(self.log_path) as f:
            lines = f.readlines()

            for index, line in enumerate(lines):
                if line == '' or index < 3:
                    continue

                # 格式化日志数据
                cols = line.strip().split("	")

                self.record_data.append({"ts": float(cols[0])})

        render([self.record_data], file_name=os.path.join(self.save_path, self.file_name))


def render(data_list, title="", file_name="统计图表.png"):
    """渲染设备的接收情况图表"""
    if not data_list:
        return
    if os.path.exists(file_name):
        logger.debug(f"已存在渲染数据：{file_name}")
        return

    # 设置主图像素跟大小
    can_id_count = len(data_list)
    render_col_count = can_id_count if can_id_count < col_count else col_count
    render_row_count = int(math.ceil(can_id_count / col_count))
    plt.rcParams['figure.dpi'] = 200
    plt.rcParams['figure.figsize'] = 10 * render_col_count, render_row_count * 6

    count = 0
    for can_id_data in data_list:
        data_count = len(can_id_data)
        if data_count <= 1:
            continue

        count += 1
        # 渲染子图图表
        plt.subplot(render_row_count, render_col_count, count)
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

        # 求均值、最大值、最小值、标准差
        avg_interval = np.mean(interval_list)
        min_interval = np.min(interval_list)
        max_interval = np.max(interval_list)
        std_interval = np.std(interval_list)

        # 渲染
        plt.title(f"count:({data_count}) time:{int(can_id_data[-1].get('ts') - can_id_data[0].get('ts'))}s std/avg:{'%.3f' % (std_interval/avg_interval)}")
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
    plt.suptitle(title, fontsize="xx-large")
    plt.savefig(file_name, dpi=200, format='png')
    plt.close()


def asc_list_from_path(path):
    """
    从路径中自动遍历识别.asc文件路径列表
    @param path:
    @return:list
    """
    if not os.path.exists(path):
        logger.error(f"{path}路径不存在")
        return

    if os.path.isfile(path) and path.endswith(".asc"):
        return [path]
    elif os.path.isdir(path):
        log_list = []
        for f in os.listdir(path):
            children_path = os.path.join(path, f)
            if children_path.endswith(".asc"):
                log_list.append(children_path)
            elif os.path.isdir(children_path):
                log_list += asc_list_from_path(children_path)
        return log_list


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='+', help='包含.asc文件的路径')
    parser.add_argument('--debug', action='store_true', help='调试模式', default=False)
    parser.add_argument('--save', '-s', help='保存统计图表文件夹路径（默认当前目录）')
    args = parser.parse_args()

    # 初始化日志输出等级
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # 初始化保存路径
    if args.save and not os.path.exists(args.save):
        args.save = None

    log_path_list = []
    for path in args.path:
        if not os.path.exists(path):
            continue
        log_path_list += asc_list_from_path(path)

    logger.debug(f"wait statistics count: {len(log_path_list)}")
    for path in log_path_list:
        task = Statistics(path, save_path=args.save)
        task.run()
    logger.warning("运行结束")
