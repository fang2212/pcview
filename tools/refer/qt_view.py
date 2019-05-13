import time
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import cv2

from multiprocessing import Process, Queue

class VideoBox(QWidget):

    def __init__(self, queue):
        QWidget.__init__(self)

        self.thread = Worker(None, queue)
        # 组件展示
        self.pictureLabel = QLabel()
        self.queue = queue
        init_image = QPixmap("cat.jpeg").scaled(self.width(), self.height())
        self.pictureLabel.setPixmap(init_image)

        control_box = QHBoxLayout()
        control_box.setContentsMargins(0, 0, 0, 0)


        layout = QVBoxLayout()
        layout.addWidget(self.pictureLabel)
        layout.addLayout(control_box)

        self.setLayout(layout)
        self.show()
        self.pictureLabel.setPixmap(init_image)
        self.thread.sinOut.connect(self.slotAdd)
        self.thread.start()
    
    def slotAdd(self, num):
        self.update()

    def update(self):
        frame = self.queue.get()
        height, width = frame.shape[:2]
        print('get', height, width)
        if frame.ndim == 3:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif frame.ndim == 2:
            rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
        temp_pixmap = QPixmap.fromImage(temp_image)
        self.pictureLabel.setPixmap(temp_pixmap)


class Qtest(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """

    def __init__(self, queue):
        Process.__init__(self)
        self.daemon = True
        self.queue = queue

    def run(self):
        inc = 0
        playCapture = cv2.VideoCapture()
        playCapture.open("resource/video.mp4")

        while playCapture.isOpened():
            success, frame = playCapture.read()
            if success:
                self.queue.put(frame)
                print(111)
            time.sleep(0.03)

class Worker(QThread):
    sinOut = pyqtSignal(str)

    def __init__(self, parent=None, queue=None):
        super(Worker, self).__init__(parent)
        self.working = True
        self.num = 0
        self.queue = queue

    def __del__(self):
        self.working = False
        self.wait()

    def run(self):
        while self.working == True:
            while self.queue.qsize()>0:
            # file_str = 'File index {0}'.format(self.num)
            # file_str = 'File index {0}'.format(qnum)
                self.num += 1
    # 发出信号
                self.sinOut.emit(str(self.num))
            time.sleep(0.02)
            # 线程休眠2秒
            # self.sleep(1)


if __name__ == "__main__":
    mapp = QApplication(sys.argv)
    queue = Queue()
    qtest = Qtest(queue)
    qtest.start()
    mw = VideoBox(queue)
    sys.exit(mapp.exec_())
