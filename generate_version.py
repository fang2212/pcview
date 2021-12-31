import os
import pathlib
import time

from git import Repo

from utils import logger


def generate_git_version():
    """
    根据git生成版本号
    Returns:

    """
    try:
        print(os.getcwd())
        repo = Repo(os.getcwd())
    except Exception as e:
        logger.error(e, exc_info=True)
        return

    commit_datatime = time.mktime(repo.head.commit.committed_datetime.timetuple())
    diff_ts = 0
    change_files = repo.index.diff(None)
    for file in change_files:
        path_tuple = pathlib.PurePath(file.b_path).parts
        if path_tuple[0] != "config":
            file_diff_ts = os.path.getmtime(file.b_path) - commit_datatime
            if file_diff_ts > diff_ts:
                diff_ts = file_diff_ts
    version = f"{repo.head.commit.committed_datetime.strftime('%Y.%m.%d')}.{repo.head.commit.hexsha[:8]}.{int(diff_ts)}\n"
    version += f"提交信息：{repo.head.commit.message.strip()}\n最后一次修改时间差：{int(diff_ts)}秒"
    file = open("./version.txt", "w+")
    file.write(version)
    file.flush()


if __name__ == "__main__":
    generate_git_version()
