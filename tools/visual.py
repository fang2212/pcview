#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/07/15
# @Author  : simon.xu
# @File    : visual.py
# @Desc    :

import os
from matplotlib import pyplot as plt
from pylab import *
import numpy as np
from random import random
import time
from collections import deque
from multiprocessing import Process, Queue

# import pickle

# plt.ion()
# fig = plt.figure()
subplots_adjust(hspace=0.000)


def get_fig():
    return plt.figure()


def close_fig(fig):
    plt.close(fig)


def match_label(label, entry):
    match = True
    spc0 = label.split('.')
    spc1 = entry.split('.')
    # print(spc0, spc1)
    for idx, spc in enumerate(spc0):
        if idx >= len(spc1):
            match = False
            break
        elif spc != spc1[idx] and spc != '*' and '[' not in spc:
            match = False
            break

        if '[' in spc:
            ids = [int(x) for x in spc[1:-1].split(',')]
            if int(spc1[idx]) not in ids:
                match = False
    return match


def scatter(fig, file_name, labels=None, ytag=None, ts0=0, start_ts=None, end_ts=None, vis=True):
    n = len(fig.axes)
    for i in range(n):
        fig.axes[i].change_geometry(n + 1, 1, i + 1)


    if n > 0:
        # print('sharex')
        ax = fig.add_subplot(n + 1, 1, n + 1, sharex=fig.axes[n - 1])
        # ax.get_shared_x_axes().join(fig.axes[n - 1], ax)
    else:
        ax = fig.add_subplot(n + 1, 1, n + 1)

    # print(fig.axes)
    print('plotting', file_name, labels)
    fig.set_size_inches(12, (n+1)*3+1)
    last_ts = 0
    # deltas = []
    data = {}
    ts = {}
    frame_id = 0
    # for l in labels:
    #     for item in labels[l]:
    #         key = l + '.' + item
    #         data[key] = []
    #         ts[key] = []
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            ts_now = float(cols[0]) + float(cols[1]) / 1000000
            # if start_ts and ts_now < start_ts:
            #     continue
            # if end_ts and ts_now > end_ts:
            #     break
            for label in labels:
                match = match_label(label, cols[2])

                if match:
                    # print('ok')
                    for idx in labels[label]:
                        key = cols[2] + '.' + idx
                        if key not in data:
                            data[key] = []
                        if key not in ts:
                            ts[key] = []
                        # print(labels[label][idx])
                        data[key].append(float(cols[3 + labels[label][idx]]))
                        ts[key].append(ts_now - ts0)
    # print(ax[fig_idx, 0])
    for item in sorted(data.keys()):
        # ax.plot(ts[item], data[item])
        ax.plot(ts[item], data[item], '.-', alpha=0.8)

    ax.legend(sorted(data.keys()))
    dur = end_ts - start_ts
    if 'TTC' not in labels:
        plt.xlim(start_ts - ts0 - 0.2 * dur, end_ts - ts0 + 0.2 * dur)
    plt.xlabel("time(s)")
    if ytag:
        plt.ylabel(ytag)
    plt.tight_layout()
    plt.grid(axis="y")
    # plt.pause(1000)
    if vis:
        plt.show()
    # ax_idx += 1


def trj_2d(fig, trjs, vis=True):
    ax = fig.add_subplot()
    # print(xlist)
    # print(ylist)
    for label in sorted(trjs.keys()):
        xlist = trjs[label]['x']
        ylist = trjs[label]['y']
        ax.plot(xlist, ylist, '.-')
    ax.legend(sorted(trjs.keys()))
    if vis:
        plt.show()


def calc_rmse(predictions, targets):
    if isinstance(predictions, list):
        p = np.array(predictions)
    else:
        p = predictions
    if isinstance(targets, list):
        t = np.array(targets)
    else:
        t = targets

    return np.sqrt(((p - t) ** 2).mean())


def esr_calib_analysis(file_name):
    from sklearn.cluster import KMeans

    fig, ax = plt.subplots()
    fig.set_size_inches(20, 12)
    print('analysis esr calib data...')
    out_file = '/tmp/log_esr_calib.txt'
    # wf = open(out_file, 'w')
    azu_rtk = []
    azu_esr = []
    with open(file_name) as rf:
        for line in rf:
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if 'esr.calib' == cols[2]:
                # print(can_port, buf, r)
                azu_rtk.append(float(cols[5]))
                azu_esr.append(float(cols[6]))
    # wf.close()
    azu_rtk_a = np.array(azu_rtk)
    azu_esr_a = np.array(azu_esr)
    rmse_list = []
    km = KMeans(10)
    km.fit(azu_rtk_a.reshape(-1, 1))
    print('centers:', km.cluster_centers_)
    print(km.labels_)
    clusters = dict()
    for idx, d in enumerate(azu_rtk):
        label = km.labels_[idx]
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(d - azu_esr[idx])

    mean_calib_list = []
    rmse_cluster_list = []
    for l in clusters:
        mean_calib = np.mean(clusters[l])
        rmse = calc_rmse(azu_rtk_a, azu_esr_a + mean_calib)
        print(l, mean_calib, rmse)
        mean_calib_list.append(mean_calib)
        rmse_cluster_list.append(rmse)
    print('mean of calibs:', np.mean(mean_calib_list))
    for dz in range(-500, 500):
        # print(dz)
        dzf = dz / 100.0
        azu_esr_ac = azu_esr_a - dzf
        rmse_list.append(calc_rmse(azu_rtk_a, azu_esr_ac))
    print(rmse_list)
    idx = rmse_list.index(min(rmse_list))
    # print(idx, )
    d_azu_cali = - 5 + idx / 100.0
    print('idx:', idx, 'cali:', d_azu_cali, 'best_rmse:', min(rmse_list))
    ax.plot(range(0, 10), km.cluster_centers_)
    ax.bar(range(0, 10), mean_calib_list)
    ax.bar(range(0, 10), rmse_cluster_list)
    ax.legend(['centers', 'mean_calib', 'rmse'])
    return os.path.abspath(out_file)


def test_color():
    x = np.arange(10)
    for i in range(5):
        plt.plot(x, x * i)

    # plt.pause(1000)
    plt.show()


class Plotter(Process):
    def __init__(self, buflen=100):
        Process.__init__(self)
        self.fig, self.ax = plt.subplots()
        self.idx = 0
        self.buflen = buflen
        self.curves = []
        self.q = Queue()

    def add_source(self, src):
        self.curves.append(src)

    def update(self, label, ts, data, interval=0.01):

        self.q.put((label, ts, data))

        self.idx += 1
        # plt.pause(interval)

    def run(self):
        curves = {}
        for lbl in self.curves:
            curves[lbl] = deque(maxlen=200)
        while True:
            if self.q.empty():
                # time.sleep(0.01)
                plt.pause(0.01)
                continue
            label, ts, data = self.q.get()
            curves[label].append((ts, data))
            self.ax.cla()
            for label in curves:
                x = [d[0] for d in curves[label]]
                y = [d[1] for d in curves[label]]
                self.ax.plot(x, y, '.', label=label)
            # self.ax.legend()
            # self.ax.pause(0.01)
            # self.ax.show()
            plt.legend()
            plt.pause(0.001)
            plt.draw()


def demo_animation():
    plotter = Plotter()
    plotter.add_source('value')
    plotter.start()
    cnt = 0
    for i in range(1000):
        d = random()
        print(d)
        plotter.update('value', cnt, d)
        cnt += 1
        # time.sleep(0.2)
    plotter.join()


if __name__ == "__main__":
    esr_calib_analysis('/home/nan/workshop/git/pc-collector/esr_clb.txt')
    samples = {'rtk.target': {'angle': 1},
               # 'lmr.obj.7': {'angle': 1},
               'lmr.obj.0': {'angle': 1},
               # 'lmr.obj.3': {'angle': 1},
               # 'lmr.obj.2': {'angle': 1},
               # 'lmr.obj.1': {'angle': 1},
               # 'lmr.obj.4': {'angle': 1},
               'esr.obj.3': {'angle': 1},
               # 'esr.obj.6': {'angle': 1},
               # 'esr.obj.48': {'angle': 1},
               # 'esr.obj.52': {'angle': 1},
               }
    # test_color()
    # visualize('/media/nan/860evo/data/20190329_esr_lmr_rtk_calib_test/20190329170909/log_sort.txt',
    #           samples,
    #           start_frame=13390, stop_frame=15400)
    # visualize('/media/nan/860evo/data/20190329_esr_lmr_rtk_calib_test/20190329172753/log_sort.txt',
    #           samples,
    #           # start_frame=23000, stop_frame=25200
    #           )

    scatter('/home/nan/workshop/git/pc-collector/esr_clb.txt', {'esr.calib': {'d_azu': 1, 'azu_rtk': 2}})

    plt.pause(1000)
    # demo_animation()
