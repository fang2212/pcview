import argparse
import json
import logging
import platform
import shutil
import sys
from multiprocessing import Queue

from config.config import dic2obj, bcl, load_cfg
from pcc import *
from sink.hub import Hub
from tools.mytools import Supervisor

machine_arch = platform.machine()

parser = argparse.ArgumentParser(description="process CVE log.")
parser.add_argument('cfg_path', nargs='?', default='config/cfg_lab.json')
parser.add_argument('-o', '--output', default=None, help="保存路径")
parser.add_argument('-d', '--debug', action="store_true", help="调试模式，可看调试信息")
parser.add_argument('-c', '--config', default=None)
parser.add_argument('-a', '--auto', help='auto recording', action="store_true")
parser.add_argument('-w', '--web', help='web ui', action="store_true")
parser.add_argument('-da', '--draw_algo', help='show algo data', action="store_true")

args = parser.parse_args()

# 初始化信息输出等级
if args.debug:
    logger.setLevel(level=logging.DEBUG)

local_cfg = dic2obj(json.load(open('config/local.json')))
if args.output:
    local_cfg.log_root = args.output
else:
    try:
        mount_root = '/mnt/'
        udevs = os.listdir(mount_root)
        if not udevs:
            raise FileNotFoundError
        dir_found = False
        for udev in udevs:
            save_path = os.path.join(mount_root, udev, 'cve_data')
            if os.path.exists(save_path):
                logger.info('found cve dir {}'.format(save_path))
                local_cfg.log_root = save_path
                dir_found = True
                break
        if not dir_found:
            logger.warning('creating cve dir')
            save_path = os.path.join(mount_root, udevs[0], 'cve_data')
            os.mkdir(save_path)
            local_cfg.log_root = save_path
    except FileNotFoundError:
        logger.error('no media folder found.')

if args.config:
    cve_conf = load_cfg(args.config)
else:
    cve_conf = load_cfg(args.cfg_path)

local_cfg = dic2obj(json.load(open('config/local.json')))
cve_conf.local_cfg = local_cfg
logger.warning("log path:{}".format(cve_conf.local_cfg.log_root))

_startup_cwd = os.getcwd()


def init_checkers(pcc):
    """
    任务执行检查，定时执行任务并获取任务状态
    :param pcc:
    :return:
    """
    supervisor = Supervisor()
    supervisor.add_check_task(pcc.hub.fileHandler.check_file)
    supervisor.add_check_task(pcc.send_online_devices, interval=0.5)
    supervisor.add_check_task(pcc.send_statistics, interval=0.5)
    supervisor.start()
    return supervisor


if args.web:  # 网页版启动方式
    import video_server


    def respawn(self=None):
        """Re-execute the current process.

        This must be called from the main thread, because certain platforms
        (OS X) don't allow execv to be called in a child thread very well.
        """
        args = sys.argv[:]
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]

        os.chdir(_startup_cwd)
        os.execv(sys.executable, args)


    video_server.set_local_path(local_cfg.log_root)
    logger.warning('{} pid:{}'.format("PCC: webui".ljust(20), os.getpid()))
    server = video_server.PccServer()
    server.start()

    # 初始化信号加载进程
    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server, draw_algo=args.draw_algo)
    pcc_thread = Thread(target=pcc.start, name='pcc_thread')
    hub.start()

    # print('-----------------------------------------------------------------------', os.getpid())
    sup = init_checkers(pcc)
    # sup.add_check_task(list_recorded_data)
    pcc_thread.start()
    while hub.is_alive():
        if pcc.stuck_cnt > 10:
            print('pcc stuck count:', pcc.stuck_cnt)
            print('PCC stuck. restarting now.')
            respawn()
        if not video_server.ctrl_q.empty():
            ctrl = video_server.ctrl_q.get()
            if ctrl['action'] == 'control':
                key = None
                if ctrl.get('cmd') == 'pause':
                    key = 32
                elif ctrl.get('cmd') == 'start':
                    pass
                elif ctrl.get('cmd') == 'reset':
                    pcc.control(ord('q'))
                    # hub = Hub(uniconf=cve_conf)
                    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf, auto_rec=False, to_web=server)
                    pcc_thread = Thread(target=pcc.start, name='pcc_thread')
                    pcc_thread.start()
                elif ctrl.get('cmd') == 'respawn':

                    hub.close()
                    time.sleep(2)
                    pcc.control(ord('q'))
                    time.sleep(2)
                    server.terminate()
                    server.join()
                    # time.sleep(5)
                    print(bcl.WARN + 'CVE processes terminated, now respawn.' + bcl.ENDC)
                    respawn()
                else:
                    key = ord(ctrl['cmd'].lower())

                if key is not None:
                    pcc.control(key)
            elif ctrl['action'] == 'replay':
                pcc.control(ord('q'))
                print('---------------------------------------------------------\n'
                      'pcc exited\n'
                      '----------------------------------------------------------')
                rlog = os.path.join(local_cfg.log_root, ctrl['obj'], 'log.txt')
                from pcc_replay import LogPlayer, prep_replay

                r_sort, cve_conf = prep_replay(rlog, ns=True)
                replayer = LogPlayer(r_sort, cve_conf, start_frame=0, loop=True)
                pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, uniconf=cve_conf, to_web=server)
                replayer.start()
                pcc_thread = Thread(target=pcc.start, name='pcc_thread')
                pcc_thread.start()
                pass
            elif ctrl['action'] == 'analyze':
                pass

            elif ctrl['action'] == 'delete':
                dir_path = os.path.join(local_cfg.log_root, ctrl['obj'])
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    print("deleted {} from web control.".format(ctrl['obj']))
                    video_server.send_records()

        else:
            time.sleep(0.1)

    server.close()
    logger.warning("main exit")

else:  # normal standalone PCC
    logger.warning('{} pid:{}'.format("PCC: normal".ljust(20), os.getpid()))
    if args.auto:
        auto_rec = True
    else:
        auto_rec = False

    hub = Hub(uniconf=cve_conf)
    pcc = PCC(hub, ipm=True, replay=False, uniconf=cve_conf, auto_rec=auto_rec, draw_algo=args.draw_algo)
    hub.start()
    sup = init_checkers(pcc)
    pcc.start()
    logger.warning('{} pid:{}'.format("PCC: normal exit".ljust(20), os.getpid()))
    # pcc.join()
