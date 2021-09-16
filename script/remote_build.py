from datetime import datetime

import paramiko
import time
import os

local_proj_root = os.path.dirname(__file__)
if local_proj_root.endswith('script'):
    pass

def line_buffered(f):
    line_buf = b''
    while not f.channel.exit_status_ready():
        line_buf += f.read(1)
        if line_buf.endswith(b'\n'):
            yield line_buf.decode()
            line_buf = b''


class SSHSession(object):
    def __init__(self, hostname, port=22, username='mini', password='mini'):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.ssh.connect(hostname=hostname, port=port, username=username, password=password)
        self.tp = self.ssh.get_transport()
        # print(self.ssh)

    def exec(self, cmd, get_pty=False):
        stdin, stdout, stderr = self.ssh.exec_command(cmd + ' 2>&1', bufsize=1)
        for line in line_buffered(stdout):
            print(line, end='')
        for line in line_buffered(stderr):
            print('err:', line)
        # return res

    def upload(self, src, dst):
        sftp = paramiko.SFTPClient.from_transport(self.tp)
        sftp.put(src, dst)

    def download(self, src, dst):
        sftp = paramiko.SFTPClient.from_transport(self.tp)
        sftp.get(src, dst)

    def close(self):
        self.ssh.close()
        self.tp.close()


def trigger_build(branch=None, local_path='.', ip=None, platform=""):
    work_dir = '/home/mini/work/pcview'
    suffix = 'cd {} && '.format(work_dir)
    print("连接ip：", ip)
    sess = SSHSession(ip, username='mini', password='mini')
    if branch:
        sess.exec(suffix + 'git checkout {}'.format(branch))
    sess.exec(suffix + 'git pull')

    sess.exec(suffix + 'bash -l -c ./pack_pcc_and_replay.sh')

    # retrieve binary
    pcc_app_local = os.path.join(local_path,
                                 'pcc_app_replay_{}_{}_{}.tar.gz'.format(platform, branch, datetime.now().strftime("%m%d")))
    sess.download(work_dir + '/dist/pcc_app.tar.gz', pcc_app_local)
    return local_path

def trigger_build_1604(branch=None, local_path='.'):
    work_dir = '/home/mini/work/pcview'
    suffix = 'cd {} && '.format(work_dir)
    sess = SSHSession('192.168.51.187', username='mini', password='mini')
    if branch:
        sess.exec(suffix + 'git checkout {}'.format(branch))
    sess.exec(suffix + 'git pull')

    # sess.exec(suffix + '/home/nan/.local/bin/pyinstaller pcc_app.spec --noconfirm')
    sess.exec(suffix + 'bash pack_pcc_and_replay.sh')
    # sess.exec(suffix + '')

    # retrieve binary
    pcc_app_local = os.path.join(local_path, 'pcc_app_replay_1604_{}_{}.tar.gz'.format(branch, datetime.now().strftime("%m%d")))
    sess.download(work_dir + '/dist/pcc_app.tar.gz', pcc_app_local)
    statistics_local = os.path.join(local_path, 'pcc_statistics_1604_{}_{}.tar.gz'.format(branch, datetime.now().strftime("%m%d")))
    sess.download(work_dir + '/dist/statistics_log.tar.gz', statistics_local)
    return local_path


def deploy_to_cve(pack_path, remote_path='/home/minieye/upgrade_temp/'):
    pack_name = os.path.basename(pack_path)
    print('deploying...', pack_name)
    sess = SSHSession('192.168.98.222', username='minieye', password='minieye')
    sess.upload(pack_path, os.path.join(remote_path, pack_name))
    suffix = 'cd {} && '.format(remote_path)
    sess.exec(suffix + 'rm -rf unzip')
    sess.exec(suffix + 'mkdir unzip')
    sess.exec(suffix + 'tar xvzf {} -C unzip'.format(pack_name))
    # sess.exec('cd {} && cp unzip/pcc_app /home/minieye/work/pcc_app/pcc_app')
    sess.exec(suffix + 'sudo service cve stop', get_pty=True)
    sess.exec(suffix + 'rm -rf /home/minieye/work/pcc_app')
    sess.exec(suffix + 'cp -r unzip/pcc_app /home/minieye/work/')
    sess.exec(suffix + 'sudo service cve start', get_pty=True)


if __name__ == "__main__":
    import argparse
    import os

    home = os.environ['HOME']
    parser = argparse.ArgumentParser(description="pcc remote build and retrieve.")
    parser.add_argument('-p', '--platform')
    parser.add_argument('-b', '--branch', default='cve-new')
    parser.add_argument('-t', '--target', default='pcc')  #
    parser.add_argument('-o', '--output', default=home)

    args = parser.parse_args()

    if args.platform == '1604':
        pack = trigger_build(args.branch, args.output, ip="192.168.51.187", platform=args.platform)
        print('retrieved pcc package at', pack)

    elif args.platform == '1804':
        pack = trigger_build(args.branch, args.output, ip="192.168.51.162", platform=args.platform)
        print('retrieved 1804 pcc package at', pack)
    else:
        pack = trigger_build(args.branch, args.output, ip="192.168.51.187", platform='1604')
        print('retrieved 1604 package at', pack)
        pack = trigger_build(args.branch, args.output, ip="192.168.51.162", platform='1804')
        print('retrieved 1804 pcc package at', pack)


    # pack = '/home/nan/release/pcc_app_1804_cve-new_1598513211.tar.gz'
    # pack = trigger_build('cve-new')

    # deploy_to_cve(pack)