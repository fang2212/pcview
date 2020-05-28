# import av
# from PIL import Image
# from io import BytesIO

AVIH_STRH_SIZE = 56
MAX_BYTES_PER_SEC = 15552000
AVI_DWFLAG = 2320
NSTREAMS = 1
SUG_BUFFER_SIZE = 1048576
AVI_DWSCALE = 1
AVI_DWQUALITY = -1
STRF_SIZE = 40
AVI_BIPLANES = 1
AVI_BITS_PER_PIXEL = 24
AVIF_KEYFRAME = 16

# class VideoWriter(object):
#     def __init__(self):
#         self.container = None
#         self.stream = None
#         self.video_path = None
#
#     def _init(self):
#         self.container = None
#         self.stream = None
#         self.video_path = None
#
#     def init_video(self, video_path):
#         self._init()
#         self.video_path = video_path
#         self.container = av.open(self.video_path, mode='w')
#         self.stream = self.container.add_stream('mjpeg', rate=20)
#         self.stream.width = 1280
#         self.stream.height = 720
#         # self.stream.pix_fmt = 'rgb565'
#
#     def insert_frame(self, jpg):
#         frame = av.VideoFrame.from_image(Image.open(BytesIO(jpg)))
#         for packet in self.stream.encode(frame):
#             self.container.mux(packet)
#
#     def finish_video(self):
#         for packet in self.stream.encode():
#             self.container.mux(packet)
#         self.container.close()
#         return self.video_path


class MJPEGWriter(object):
    video_path = None
    fp = None
    fsize = 0
    width = 0
    height = 0
    fps = 0
    wcnt = 0
    # riff_size_idx = 0
    frame_num_idxes = []
    movie_idx = 0
    frame_num = 0
    frame_offset = []
    frame_size = []
    chunk_idxes = []

    def __init__(self, video_path, width, height, fps):
        self.init_video(video_path, width, height, fps)

    def init_video(self, video_path, width, height, fps):
        self.video_path = video_path
        self.fp = open(video_path, 'wb')
        self.width = width
        self.height = height
        self.fps = fps
        # self.riff_size_idx = 0
        self.frame_num_idxes = []
        self.movie_idx = 0
        self.frame_num = 0
        self.frame_offset = []
        self.frame_size = []
        self.chunk_idxes = []

    def _put(self, b):
        if self.fp is not None:
            self.fp.write(b)
            self.wcnt += len(b)

    def _put_at(self, p, b):
        if self.fp is not None:
            currentfp = self.fp.tell()
            self.fp.seek(p)
            self.fp.write(b)
            self.fp.seek(currentfp)

    def _padding(self, ali):
        mod = self.fp.tell() % ali
        if mod == 0:
            return
        pad_size = ali - mod
        for i in range(pad_size):
            self._put(b'\x00')

    def _chunk(self, b):
        self._put(b)
        self.chunk_idxes.append(self.fp.tell())
        self._put(b'\x00\x00\x00\x00')

    def _end_chunk(self):
        cpos = self.fp.tell()
        fpos = self.chunk_idxes.pop()
        self.fp.seek(fpos)
        self._put((cpos-fpos-4).to_bytes(4, 'little'))
        self.fp.seek(cpos)

    # def _start_chunk(self):
    def write_header(self):
        # RIFF
        self._chunk(b'RIFF')
        # self._put(b'RIFF')
        # self.riff_size_idx = self.fp.tell()
        # self._put(b'\x00\x10\x00\x00')
        self._put(b'AVI\x20')
        self._put(b'LIST')
        self._put(b'\xdc\x00\x00\x00')
        self._put(b'hdrl')
        self._put(b'avih')
        self._put(AVIH_STRH_SIZE.to_bytes(4, 'little'))
        self._put(int(1000000/self.fps).to_bytes(4, 'little'))
        self._put(MAX_BYTES_PER_SEC.to_bytes(4, 'little'))
        self._put(b'\x00\x00\x00\x00')
        self._put(AVI_DWFLAG.to_bytes(4, 'little'))
        self.frame_num_idxes.append(self.fp.tell())
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(NSTREAMS.to_bytes(4, 'little'))
        self._put(SUG_BUFFER_SIZE.to_bytes(4, 'little'))
        self._put(self.width.to_bytes(4, 'little'))
        self._put(self.height.to_bytes(4, 'little'))
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        # strh
        self._put(b'LIST')
        self._put(b'\x74\x00\x00\x00')
        self._put(b'strl')
        self._put(b'strh')
        self._put(AVIH_STRH_SIZE.to_bytes(4, 'little'))
        self._put(b'vids')
        self._put(b'MJPG')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(AVI_DWSCALE.to_bytes(4, 'little'))
        self._put(self.fps.to_bytes(4, 'little'))
        self._put(b'\x00\x00\x00\x00')
        self.frame_num_idxes.append(self.fp.tell())
        self._put(b'\x00\x00\x00\x00')
        self._put(SUG_BUFFER_SIZE.to_bytes(4, 'little'))
        self._put(AVI_DWQUALITY.to_bytes(4, 'little', signed=True))
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(self.width.to_bytes(2, 'little'))
        self._put(self.height.to_bytes(2, 'little'))
        # strf
        self._put(b'strf')
        self._put(STRF_SIZE.to_bytes(4, 'little'))
        self._put(STRF_SIZE.to_bytes(4, 'little'))
        self._put(self.width.to_bytes(4, 'little'))
        self._put(self.height.to_bytes(4, 'little'))
        self._put(AVI_BIPLANES.to_bytes(2, 'little'))
        self._put(AVI_BITS_PER_PIXEL.to_bytes(2, 'little'))
        self._put(b'MJPG')
        self._put((self.width*self.height*3).to_bytes(4, 'little'))
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        self._put(b'LIST')
        self._put(b'\x14\x00\x00\x00')
        self._put(b'odml')
        self._put(b'dmlh')
        self._put(b'\x08\x00\x00\x00')
        self.frame_num_idxes.append(self.fp.tell())
        self._put(b'\x00\x00\x00\x00')
        self._put(b'\x00\x00\x00\x00')
        # JUNK
        self._put(b'JUNK')
        self._put(b'\x08\x0f\x00\x00')
        junk = bytes(0x0f08)
        self._put(junk)
        # movi
        self._chunk(b'LIST')
        # self._put(b'LIST')
        # self._put(b'\x00\x00\x00\x00') # size modify later
        self.movie_idx = self.fp.tell()
        self._put(b'movi')

    def write_frame(self, jpg):
        if len(jpg) == 0:
           print('write frame error: jpg len is 0.')
        cptr = self.fp.tell()
        self._chunk(b'00dc')
        # self._put(b'00dc')
        # self._put(b'\x00\x00\x01\x00')  # size modify later
        self._put(jpg)
        self._padding(4)
        self.frame_offset.append(cptr-self.movie_idx)
        self.frame_size.append(self.fp.tell()-cptr-8)
        self.frame_num += 1
        self._end_chunk()

    def write_index(self):
        self._chunk(b'idx1')
        for i in range(self.frame_num):
            self._put(b'00dc')
            self._put(AVIF_KEYFRAME.to_bytes(4, 'little'))
            self._put(self.frame_offset[i].to_bytes(4, 'little'))
            self._put(self.frame_size[i].to_bytes(4, 'little'))
        self._end_chunk()

    def flush(self):
        if self.fp:
            self.fp.flush()

    def finish_video(self):
        if not self.fp:
            return
        self._end_chunk()  # movi
        self.write_index()
        cpos = self.fp.tell()
        for idx in self.frame_num_idxes:
            self.fp.seek(idx)
            self._put(self.frame_num.to_bytes(4, 'little'))
        self.fp.seek(cpos)

        self._end_chunk()  # RIFF
        self.fp.flush()
        self.fp.close()

    def release(self):
        self.finish_video()


if __name__ == "__main__":
    import os
    def jpeg_extractor(video_dir):
        """
        This generator extract jpg from each of the video files in the directory.
        :param video_dir:
        :return: frame_id: rolling counter of the frame from FPGA (if valid, synced with video name)
                 jpg: raw jpg bytes
        """
        buf = b''
        buf_len = int(2 * 1024 * 1024)
        file_done = False
        video_files = sorted([x for x in os.listdir(video_dir) if x.endswith('.avi')])
        for file in video_files:
            print('start reading video:', file)
            file_done = False
            fcnt = 0
            fid = int(file.split('.')[0].split('_')[1])
            with open(os.path.join(video_dir, file), 'rb') as vf:
                while True:
                    a = buf.find(b'\xff\xd8')
                    b = buf.find(b'\xff\xd9')
                    while a == -1 or b == -1:
                        read = vf.read(buf_len)
                        if len(read) == 0:
                            file_done = True
                            buf = b''
                            print('video file {} comes to an end. {} frames extracted'.format(file, fcnt))
                            # print(a, b)
                            break
                        buf += read
                        if a == -1:
                            a = buf.find(b'\xff\xd8')
                        if b == -1:
                            b = buf.find(b'\xff\xd9')

                    if file_done:
                        break
                    # print(fid, a, b)
                    jpg = buf[a:b + 2]
                    buf = buf[b + 2:]
                    fcnt += 1
                    # fid = int.from_bytes(jpg[24:28], byteorder="little")
                    if not jpg:
                        print('extracted empty frame:', fid, a, b)
                    yield fid, jpg
                    if fid is not None:
                        fid = None


    jpgs = jpeg_extractor('/home/nan/data/temp')
    mw = MJPEGWriter('/home/nan/data/pcc_test/test.avi', 1280, 720, 20)
    mw.write_header()
    for fid, jpg in jpgs:
        mw.write_frame(jpg)
    mw.finish_video()