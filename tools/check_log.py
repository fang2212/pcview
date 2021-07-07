import argparse
import logging
import os
import time
from prettytable import PrettyTable

x = PrettyTable()

logger = logging.getLogger(__name__)
fh = logging.StreamHandler()
fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s： %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

def log_list_from_path(path):
    """
    从路径中自动遍历识别log.txt文件路径列表
    @param path:
    @return:list
    """
    if not os.path.exists(path):
        logger.error(f"{path}路径不存在")
        return

    if os.path.isfile(path) and os.path.split(path)[-1] == "log.txt":
        return [path]
    elif os.path.isdir(path):
        log_path = os.path.join(path, "log.txt")
        if os.path.exists(log_path):
            return [log_path]
        log_list = []
        for f in os.listdir(path):
            children_path = os.path.join(path, f)
            if os.path.isdir(children_path):
                log_list += log_list_from_path(children_path)
        return log_list


def check_log(log_path, check_tpl=None):
    """
    检查log.txt的设备信号
    @param path: log.txt路径
    @param check_tpl: 检查模板
    @return:
    """
    device_map = {}
    id_map = {}

    with open(log_path) as f:
        lines = f.readlines()

        for pos, line in enumerate(lines):
            if line == '':
                continue

            # 格式化日志数据
            cols = line.strip().split(" ")
            device_name = cols[2]
            device_id = cols[3]

            if not device_map.get(device_name):
                device_map[device_name] = (float(cols[0]) + float(cols[1]) / 1e6, pos)
            if not id_map.get(device_id) and check_tpl:
                id_map[device_id] = (float(cols[0]) + float(cols[1]) / 1e6, pos)

        if check_tpl:
            not_has = []
            with open(check_tpl) as cf:
                lines = cf.readlines()

                # 逐行对比设备信号是否齐全
                for line in lines:
                    line = line.strip()
                    if line == '':
                        continue
                    if line.startswith("0x"):
                        if not id_map.get(line):
                            not_has.append(line)
                    else:
                        if not device_map.get(line):
                            not_has.append(line)

                if not_has:
                    x.field_names = ["缺失信号"]
                    for device in not_has:
                        x.add_row([device])
                    x.align = "l"
                    logger.error("信号出现缺失：\n"+x.get_string())
                    return

        print("设备信号接收正常")
        x.field_names = ["设备名", "开始行数", "开始接收时间"]
        for device in device_map:
            x.add_row([device, device_map[device][1], time.strftime('%H:%M:%S', time.localtime(device_map[device][0]))])
        x.align = "l"
        print(x)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='+', help='包含log.txt的路径')
    parser.add_argument('--debug', action='store_true', help='调试模式', default=False)
    args = parser.parse_args()

    # 初始化日志输出等级
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    log_path_list = []
    for path in args.path:
        if not os.path.exists(path):
            continue
        log_path_list += log_list_from_path(path)

    # 检查模板
    check_template = os.path.join(os.getcwd(), "check_list.txt")
    if not os.path.exists(check_template):
        check_template = None

    for path in log_path_list:
        check_log(path, check_tpl=check_template)
        logger.warning("运行结束")