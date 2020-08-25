import paramiko
import time


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

    def exec(self, cmd):
        stdin, stdout, stderr = self.ssh.exec_command(cmd + ' 2>&1', bufsize=1)
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
    sess.download(work_dir + '/dist/pcc_app.tar.gz', '/home/nan/release/pcc_app_1804_{}_{}.tar.gz'.format(branch, int(time.time())))


if __name__ == "__main__":
    trigger_build('cve-new')