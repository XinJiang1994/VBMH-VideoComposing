import json
import sys
import cv2
import os
from enum import Enum
import numpy as np
from tqdm import tqdm
import time


from utils import composite, composite4exec


class Controller(Enum):
    TIMER = 1
    SLIDER = 2


class Video():

    def __init__(self, root, target_vname):
        super(Video, self).__init__()
        self.root = root
        self.current_target = target_vname

        self.frame = None  # 存图片
        self.frame2 = None
        self.frame1 = None
        self.frame_pha = None
        self.frame_pha2 = None
        self.frame_count_main = 0
        self.frame_count_distract = 0
        self.cap = None
        self.cap_pha = None
        self.cap_distract = None
        self.cap_pha_distract = None
        self.init_cap()
        self.init_writer(self.current_target)
        self.start_compositing()

    def read_compositingParams(self):
        json_filename = os.path.join(
            'Params', self.current_target.replace('.mp4', '.json'))
        file_json = open(json_filename)
        self.params = json.load(file_json)

    def init_cap(self):
        """ Slot function to start the progamme
            """
        # videoName, _ = QFileDialog.getOpenFileName(
        #     self, "Open", self.root, "*.mp4;;All Files(*)")
        target_vname0 = self.current_target
        self.read_compositingParams()

        target_vname = os.path.join(self.root, 'fgr', target_vname0)
        target_pha_vname = os.path.join(self.root, 'pha', target_vname0)
        distract_vname0 = self.params['distract']
        distract_vname = os.path.join(self.root, 'fgr', distract_vname0)
        distract_pha_vname = os.path.join(self.root, 'pha', distract_vname0)

        if self.cap != None:
            self.cap.release()
        if self.cap_pha != None:
            self.cap_pha.release()
        if self.cap_distract != None:
            self.cap_distract.release()
        if self.cap_pha_distract != None:
            self.cap_pha_distract.release()

        if target_vname != "":  # “”为用户取消
            self.cap = cv2.VideoCapture(target_vname)
            self.cap_pha = cv2.VideoCapture(target_pha_vname)
            self.frame_count_main = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.target_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.target_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.frame_idx = 0

            self.cap_distract = cv2.VideoCapture(distract_vname)
            self.cap_pha_distract = cv2.VideoCapture(distract_pha_vname)

            self.frame_count_distract = int(
                self.cap_distract.get(cv2.CAP_PROP_FRAME_COUNT))

    def init_writer(self, targe_name):
        dir_fgr_com = os.path.join(self.root, 'fgr_com')
        dir_pha_com = os.path.join(self.root, 'pha_com')
        if not os.path.exists(dir_fgr_com):
            os.mkdir(dir_fgr_com)
        if not os.path.exists(dir_pha_com):
            os.mkdir(dir_pha_com)
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        fps = 30.0
        save_path_v = os.path.join(dir_fgr_com, targe_name)
        save_path_pha = os.path.join(dir_pha_com, targe_name)
        v_size = (self.target_w, self.target_h)
        self.video_writer = cv2.VideoWriter(save_path_v, fourcc, fps, v_size)
        self.pha_writer = cv2.VideoWriter(save_path_pha, fourcc, fps, v_size)

    def start_compositing(self):

        if self.cap is None or self.cap_pha is None or self.cap_distract is None:
            print("!!!!!!!! Something is error, some cap is not opened")
            exit(1)
        self.frame_idx = 0
        while self.cap.isOpened() and self.cap_pha.isOpened() and self.cap_distract.isOpened() and self.cap_pha_distract.isOpened():

            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
            self.cap_pha.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
            self.cap_distract.set(cv2.CAP_PROP_POS_FRAMES,
                                  self.frame_idx % (self.frame_count_distract-1))  # don't let it to the end or the cap will be closed
            self.cap_pha_distract.set(cv2.CAP_PROP_POS_FRAMES,
                                      self.frame_idx % (self.frame_count_distract-1))

            # print('----', self.sl.value())
            ret0, self.frame1 = self.cap.read()
            ret1, self.frame_pha1 = self.cap_pha.read()
            ret2, self.frame2 = self.cap_distract.read()
            ret3, self.frame_pha2 = self.cap_pha_distract.read()
            if ret0 and ret1 and ret2 and ret3:
                frame1 = cv2.cvtColor(self.frame1, cv2.COLOR_BGR2RGB)
                frame2 = cv2.cvtColor(self.frame2, cv2.COLOR_BGR2RGB)
                st = time.time()
                frame, pha_merged = composite4exec(
                    frame1,  frame2, self.frame_pha1/255, self.frame_pha2/255, self.params)
                print('com time cost: ', time.time()-st)
                # write the result to mp4
                self.save_results(frame, pha_merged)
                if not run_on_background:
                    cv2.imshow('Com result', cv2.cvtColor(
                        frame, cv2.COLOR_RGB2BGR))
                    cv2.waitKey(1)

                self.frame_idx += 1

            elif self.frame_idx == self.frame_count_main-1:
                print('***Successfully finished target: ', self.current_target)
                self.cap.release()
                self.cap_distract.release()
                self.cap_pha.release()
                self.cap_pha_distract.release()
            else:
                print("### Some Caps might have been closed accidently.")
                self.cap.release()
                self.cap_distract.release()
                self.cap_pha.release()
                self.cap_pha_distract.release()
        self.video_writer.release()
        self.pha_writer.release()

    def save_results(self, frame, pha_merged):
        '''
            frame: a uint8 array, the value of which is from 0 to 255
            pha_merged: a float array, , the value of which is from 0 to 1
        '''
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.video_writer.write(frame)
        self.pha_writer.write(np.uint8(pha_merged*255))


if __name__ == "__main__":
    run_on_background = False

    v_root = '/Users/jiangxin/Project/Dataset/VideoMatte240K/train'
    target_vnames = [
        # '0000.mp4',
        '0003.mp4',
        #  '0006.mp4',
        #  '0007.mp4',
        #  '0008.mp4',
        #  '0010.mp4',
        #  '0013.mp4',
        #  '0022.mp4',
        #  '0023.mp4',
        #  '0024.mp4',
        #  '0025.mp4',
        #  '0026.mp4',
        #  '0027.mp4',
        #  '0028.mp4',
        #  '0032.mp4',
        #  '0033.mp4',
        #  '0034.mp4',
        #  '0037.mp4',
        #  '0038.mp4',
        #  '0039.mp4',
        #  '0040.mp4',
        #  '0042.mp4',
        #  '0046.mp4',
        #  '0047.mp4',
        #  '0050.mp4',
        #  '0051.mp4',
        #  '0062.mp4',
        #  '0063.mp4',
        #  '0064.mp4',
        #  '0067.mp4',
        #  '0068.mp4',
        #  '0069.mp4',
        #  '0072.mp4',
        #  '0073.mp4',
        #  '0075.mp4',
        #  '0076.mp4',
        #  '0079.mp4',
        #  '0081.mp4',
        #  '0082.mp4',
        #  '0084.mp4',
        #  '0085.mp4',
        #  '0090.mp4',
        #  '0092.mp4',
        #  '0096.mp4',
        #  '0097.mp4',
        #  '0098.mp4',
        #  '0099.mp4',
        #  '0101.mp4',
        #  '0102.mp4',
        #  '0103.mp4',
        #  '0104.mp4',
        #  '0109.mp4',
        #  '0110.mp4',
        #  '0120.mp4',
        #  '0129.mp4',
        #  '0132.mp4',
        #  '0133.mp4',
        #  '0134.mp4',
        #  '0135.mp4',
        #  '0136.mp4',
        #  '0137.mp4',
        #  '0138.mp4',
        #  '0139.mp4',
        #  '0142.mp4',
        #  '0144.mp4',
        #  '0145.mp4',
        #  '0146.mp4',
        #  '0147.mp4',
        #  '0150.mp4',
        #  '0151.mp4',
        #  '0153.mp4',
        #  '0154.mp4',
        #  '0155.mp4',
        #  '0156.mp4',
        #  '0157.mp4',
        #  '0158.mp4',
        #  '0159.mp4',
        #  '0160.mp4',
        #  '0161.mp4',
        #  '0162.mp4',
        #  '0163.mp4',
        #  '0169.mp4',
        #  '0170.mp4',
        #  '0172.mp4',
        #  '0173.mp4',
        #  '0175.mp4',
        #  '0178.mp4',
        #  '0180.mp4',
        #  '0181.mp4',
        #  '0182.mp4',
        #  '0183.mp4',
        #  '0184.mp4',
        #  '0185.mp4',
        #  '0186.mp4',
        #  '0187.mp4',
        #  '0188.mp4',
        #  '0189.mp4',
        #  '0191.mp4',
        #  '0192.mp4',
        #  '0195.mp4',
        #  '0196.mp4',
        #  '0198.mp4',
        '0200.mp4', ]
    for target_vname in tqdm(target_vnames):
        my = Video(v_root, target_vname)
    sys.exit(app.exec_())
