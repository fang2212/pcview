import paramiko
import time
import os


def line_buffered(f):
    line_buf = b''
    while not f.channel.exit_status_ready():
        line_buf += f.read(1)
        if line_buf.endswith(b'\n'):
            yield line_buf.decode()
            line_buf = b''


class SSHSession(object):
    def __init__(self, hostname, port=22, username='minieye', password='minieye'):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.ssh.connect(hostname=hostname, port=port, username=username, password=password)
        self.tp = self.ssh.get_transport()
        # print(self.ssh)

    def exec(self, cmd, get_pty=False):
        stdin, stdout, stderr = self.ssh.exec_command(cmd + ' 2>&1', get_pty=get_pty)
        for line in line_buffered(stdout):
            print(line, end='')
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


def trigger_build(branch=None):
    work_dir = '/home/nan/work/pcview'
    suffix = 'cd {} && '.format(work_dir)
    sess = SSHSession('192.168.50.104', username='nan', password='199116')
    if branch:
        sess.exec(suffix + 'git checkout {}'.format(branch))
    sess.exec(suffix + 'git pull')
    sess.exec(suffix + './pack_pcc.sh')

    # retrieve binary
    local_path = '/home/nan/release/pcc_app_1804_{}_{}.tar.gz'.format(branch, int(time.time()))
    sess.download(work_dir + '/dist/pcc_app.tar.gz', local_path)
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
    pack = '/home/nan/release/pcc_app_1804_cve-new_1598513211.tar.gz'
    # pack = trigger_build('cve-new')
    deploy_to_cve(pack)