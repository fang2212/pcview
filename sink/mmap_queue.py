import mmap
import os
import time
import pickle
from multiprocessing import Value, Lock

from utils import logger


class MMAPQueue:

    def __init__(self, size):
        self.mmap = mmap.mmap(-1, size, access=os.O_RDWR)       # mmap内存对象
        self.head = Value('L', 0)           # 头指针
        self.tail = Value('L', 0)           # 尾指针
        self.mmap_size = size               # 队列大小
        self.count = Value('L', 0)          # 队列中已写字节量
        self.lock = Lock()
        self.queue_size = Value('L', 0)     # 队列消息数量

        self.msg_end_tag = b'$MMAPEND$'     # 消息结尾标记
        self.msg_end_tag_len = len(self.msg_end_tag)    # 消息结尾标记长度

    def put(self, msg, block=True):
        data = pickle.dumps(msg)
        data_len_info = len(data).to_bytes(4, byteorder='big')
        content = data_len_info + data + data_len_info + self.msg_end_tag       # 完整的消息组成：内容长度(4byte)+内容+内容长度(4byte)+结尾标记
        content_len = len(content)

        while block and self.count.value + content_len > self.mmap_size:
            time.sleep(0.001)

        self.lock.acquire()
        write_result = self.write(content)
        self.lock.release()
        return write_result

    def get(self, block=True, time_out=None):
        if self.count.value == 0:
            if block:       # 是否阻塞
                st = time.time()
                while self.count.value == 0:
                    if time_out and time.time() - st < time_out:  # 是否设置超时时间
                        return
                    time.sleep(0.001)
            else:
                return

        self.lock.acquire()
        # before_head = self.head.value
        # end_index = self.find(b'$MMAPEND$')
        # if end_index == -1:
        #     raise IndexError("未找到结尾数据 MMAPQueue出现异常")
        # content_len = self.long(self.head.value, end_index) + 4    # len(b'$MMAPEND$')=9 len(header_info)=4 read_index + end_index + 9 - 1 - 4
        head_info = self.remove(4)      # 获取消息头部数据（消息长度）
        data_len_head = int.from_bytes(head_info, byteorder='big')
        msg = self.remove(data_len_head)
        end_info = self.remove(4)
        data_len_end = int.from_bytes(end_info, byteorder='big')
        if data_len_head != data_len_end:
            logger.error("head info not equal to end info, head info:{} end info:{}".format(data_len_head, data_len_end))

        if content_len != data_len:
            logger.error("content 长度 != head_info长度 content len:{} head_len:{}".format(content_len, data_len))
            data_len = content_len
        # print(f"offset:{content_len - data_len} content len:{content_len} data_len:{data_len}")
        msg = self.remove(data_len, locking=True)
        self.lock.release()
        try:
            data = pickle.loads(msg)
            return data
        except Exception as e:
            logger.error("开始位置：{}, 准备取数据长度：{}, 取到的数据长度：{}, 数据内容：{}".format(before_head, data_len, len(msg), f'{msg[:30]}...{msg[-30:]}' if len(msg) > 100 else msg))
            logger.error("无法正常解析数据 MMAPQueue出现异常")
            return

    def write(self, content):
        write_len = len(content)
        if self.count.value + write_len > self.mmap_size:
            return False

        if self.tail.value + write_len >= self.mmap_size:
            end_num = (self.tail.value + write_len) % self.mmap_size
            front_num = write_len - end_num

            self.mmap.seek(self.tail.value)
            self.mmap.write(content[:front_num])
            self.mmap.seek(0)
            self.mmap.write(content[front_num:])
            self.tail.value = end_num
        else:
            self.mmap.seek(self.tail.value)
            self.mmap.write(content)
            self.tail.value += write_len
        self.queue_size.value += 1
        self.count.value += write_len

        return True

    def remove(self, num):
        if self.count.value <= 0:
            return False
        else:
            if num > self.count.value:
                logger.error("lost data, num:{}, count:{}".format(num, self.count.value))
                num = self.count.value
            if self.head.value + num >= self.mmap_size:     # 获取长度超出循环，进行模运算获取剩余数据的数量
                end_num = (self.head.value + num - 1) % self.mmap_size
                content = self.mmap[self.head.value:]
                if end_num > 0:
                    content += self.mmap[:end_num]
                self.head.value = end_num
            else:
                content = self.mmap[self.head.value:self.head.value+num]
                self.head.value += num
                if self.head.value == self.mmap_size - 1:
                    self.head.value = 0
            self.count.value -= num
            self.queue_size.value -= 1
            return content

    def reset(self, num):
        """
        回滚固定长度的数据
        @param num:
        @return:
        """
        if self.full():
            return
        if self.count.value + num > self.mmap_size:
            return

        if self.head.value - num < 0:
            end_num =

    def full(self):
        return self.count.value >= self.mmap_size

    def empty(self):
        return self.count.value == 0

    def size(self):
        return self.count

    def qsize(self):
        return self.queue_size.value

    def clear(self):
        self.lock.acquire()
        self.head.value = 0
        self.tail.value = 0
        self.count.value = 0
        self.queue_size.value = 0
        self.lock.release()

    def find(self, content):
        self.mmap.seek(self.head.value)
        find_index = self.mmap.find(content)
        if find_index == -1:
            # 如果从队列头开始到内存空间结尾都没找到，进行拼接后循环数据查找
            content_len = len(content)
            bytes_str = self.mmap[-content_len:]
            bytes_str += self.mmap[:content_len]
            find_index = bytes_str.find(content)
            if find_index != -1:
                return find_index - content_len if find_index > content_len - 1 else self.mmap_size - content_len + find_index
            else:
                self.mmap.seek(0)
                find_index = self.mmap.find(content)
                return -1 if find_index > self.tail.value else find_index
        return find_index

    def long(self, start=0, end=-1):
        if end == -1:
            return self.mmap_size - self.head.value
        else:
            if end < -1:
                end = self.mmap_size - (-end) + 1
            if start < end:
                return end - start + 1
            else:
                front_num = self.mmap_size - self.head.value
                return front_num + end + 1


if __name__ == "__main__":
    m = MMAPQueue(30)
    n = 0

    while True:
        if n % 2 == 0:
            m.put(b'abc', block=True)
        m.put(b'1234')
        msg = m.get()
        if msg:
            print('get:', msg)

        # m.get(3)
        n += 1
        if n > 18:
            break
        # if not m.get(2):
        #     break
