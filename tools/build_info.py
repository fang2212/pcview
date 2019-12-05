import time
import subprocess

if __name__ == "__main__":
    build_time = time.ctime()
    label = subprocess.check_output(["git", "describe"]).strip().decode()
    with open('build_info.txt', 'w') as wf:
        wf.write(build_time+'\n')
        wf.write(label+'\n')
