import os

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


if __name__ == '__main__':
    test_list = [1,2,3,4,5,6,7]
    print(test_list[:-4])
    print(test_list[-4:])
    # print(log_list_from_path("/mnt/cve_drive01/"))
