import time
import subprocess


def get_git_label():
    return subprocess.check_output(["git", "describe"]).strip().decode()


if __name__ == "__main__":
    build_time = time.ctime()
    label = get_git_label()
    with open('build_info.txt', 'w') as wf:
        wf.write(build_time+'\n')
        wf.write(label+'\n')
