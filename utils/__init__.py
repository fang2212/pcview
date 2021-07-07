import os

import cv2

from utils.log import logger


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


def get_source_info_opencv(source_name):
    return_value = 0
    try:
        cap = cv2.VideoCapture(source_name)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH )
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        print("source: {} \nwidth:{} \nheight:{} \nfps:{} \nnum_frames:{}".format(source_name, width, height, fps, num_frames))
    except (OSError, TypeError, ValueError, KeyError, SyntaxError) as e:
        print("init_source:{} error. {}\n".format(source_name, str(e)))
        return_value = -1
    return return_value


if __name__ == '__main__':
    path = "/home/li/work/video"
    for f in os.listdir(path):
        print("==="*6)
        print("file:", f)
        get_source_info_opencv(os.path.join(path, f))
    # print(log_list_from_path("/mnt/cve_drive01/"))
