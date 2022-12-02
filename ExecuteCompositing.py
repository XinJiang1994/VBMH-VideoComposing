import json
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import cv2
from PyQt5.QtCore import QTimer
import os
from enum import Enum
import numpy as np

from utils import composite, composite_with_pha


class Controller(Enum):
    TIMER = 1
    SLIDER = 2


class Video(QWidget):

    def __init__(self, root, target_vnames):
        super(Video, self).__init__()
        self.root = root

        self.frame = None  # 存图片
        self.frame2 = None
        self.frame_pha = None
        self.frame_pha2 = None
        self.frame_count_main = 0
        self.frame_count_distract = 0
        self.cap = None
        self.cap_pha = None
        self.cap_distract = None
        self.cap_pha_distract = None
        self.timer_camera = QTimer()  # 定义定时器

        pos_unit = 90

        # 外框
        # self.resize(900, 650)
        self.resize(1366, 960)
        self.setWindowTitle("Compostite Video")
        # 图片label
        self.label = QLabel(self)
        self.label.setText("Waiting for video...")
        self.label.setFixedSize(1080, 720)  # width height
        self.label.move(0, 0)
        self.label.setStyleSheet("QLabel{background:gray;}"
                                 "QLabel{color:rgb(100,255,100);font-size:15px;font-weight:bold;font-family:宋体;}"
                                 )

        # select target videos
        self.label_target = QLabel(self)
        self.label_target.setText("Target:")
        self.label_target.setFixedSize(65, 20)  # width height
        self.label_target.move(1085, 10)

        self.target_videos = QComboBox(self)
        self.target_videos.addItems(target_vnames)
        self.target_videos.move(1*pos_unit-10+1085, 10)
        # Preview Target video
        self.label_target_preview = QLabel(self)
        self.label_target_preview.setText("Waiting for Target video...")
        self.label_target_preview.setFixedSize(260, 160)  # width height
        self.label_target_preview.move(1085, 40)
        self.label_target_preview.setStyleSheet("QLabel{background:gray;}"
                                                "QLabel{color:rgb(100,255,100);font-size:15px;font-weight:bold;font-family:宋体;}"
                                                )

        # Preview Distracting video
        self.label_distract_preview = QLabel(self)
        self.label_distract_preview.setText("Waiting for Distracting video...")
        self.label_distract_preview.setFixedSize(260, 160)  # width height
        self.label_distract_preview.move(1085, 240)
        self.label_distract_preview.setStyleSheet("QLabel{background:gray;}"
                                                  "QLabel{color:rgb(100,255,100);font-size:15px;font-weight:bold;font-family:宋体;}"
                                                  )

        # 开启视频按键
        self.isPlaying = False
        self.btn = QPushButton(self)
        self.btn.setText("Open")
        self.btn.move(1085+100, 410)
        self.btn.clicked.connect(self.slotStart)
        self.btn.setStyleSheet(
            "QPushButton{background:orange;}")

        ## ******* Play and Stop buttong ***********#####
        ps_group_x_pos = 400
        # 检测按键
        self.btn_preview = QPushButton(self)
        self.btn_preview.setText("Start Compositing")
        self.btn_preview.move(5*pos_unit-40+ps_group_x_pos, 740)
        self.btn_preview.setStyleSheet(
            "QPushButton{background:red;}")  # 没检测红色，检测绿色
        self.btn_preview.clicked.connect(self.change_playing_status)
        # 关闭视频按钮
        self.btn_stop = QPushButton(self)
        self.btn_stop.setText("Stop")
        self.btn_stop.move(6*pos_unit+ps_group_x_pos, 740)
        self.btn_stop.clicked.connect(self.slotStop)

        self.frame_idx = 0

        # progress bar for playing video
        self.sl = QSlider(Qt.Horizontal, self)
        self.sl.setMinimum(0)
        self.sl.setMaximum(0)
        self.sl.setValue(self.frame_idx)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(10)
        self.sl.setGeometry(10, 740, 760, 40)

        self.controller = Controller.TIMER

    def read_compositingParams(self):
        json_filename = os.path.join(
            'Params', self.current_target.replace('.mp4', '.json'))
        self.params = json.load(json_filename)

    def slotStart(self):
        """ Slot function to start the progamme
            """
        self.init_compositingParams()
        # videoName, _ = QFileDialog.getOpenFileName(
        #     self, "Open", self.root, "*.mp4;;All Files(*)")
        target_vname0 = self.target_videos.currentText()
        self.current_target = target_vname0
        target_vname = os.path.join(self.root, 'fgr', target_vname0)
        target_pha_vname = os.path.join(self.root, 'pha', target_vname0)
        distract_vname = self.params['distract']
        distract_vname = os.path.join(self.root, 'fgr', distract_vname)
        distract_pha_vname = os.path.join(self.root, 'pha', distract_vname)

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
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.label.setText(target_vname)
            self.sl.setMaximum(self.frame_count_main-1)
            self.frame_idx = 0
            self.sl.setValue(self.frame_idx)

            self.cap_distract = cv2.VideoCapture(distract_vname)
            self.cap_pha_distract = cv2.VideoCapture(distract_pha_vname)

            self.frame_count_distract = int(
                self.cap_distract.get(cv2.CAP_PROP_FRAME_COUNT))
            self.openFrame()

    def slotStop(self):
        """ Slot function to stop the programme
            """
        if self.isPlaying:
            self.change_playing_status()

        if self.cap != None:
            self.cap.release()
            self.timer_camera.stop()   # 停止计时器
            self.label.setText("This video has been stopped.")
            self.label.setStyleSheet("QLabel{background:gray;}"
                                     "QLabel{color:rgb(100,255,100);font-size:15px;font-weight:bold;font-family:宋体;}"
                                     )
            if self.cap_distract != None:
                self.cap_distract.release()
            if self.cap_pha != None:
                self.cap_pha.release()
        else:
            Warming = QMessageBox.warning(
                self, "Warming", "Push the left upper corner button to Quit.", QMessageBox.Yes)

    def save_params(self):

        self.compositingParams['distract'] = self.distracting_videos.currentText(
        )
        save_folder = 'Params'
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)
        fname = os.path.join(
            save_folder, self.target_videos.currentText().replace('.mp4', '')+'.json')
        with open(fname, 'w') as fp:
            json.dump(self.compositingParams, fp)
        QMessageBox.about(self, "Information",
                          "Save success!")

    def openFrame(self):
        """ Slot function to capture frame and process it
            """
        if self.cap is None or self.cap_pha is None or self.cap_distract is None:
            QMessageBox.about(self, "Operate Failed",
                              "Please open video first!")
            return

        if (self.cap.isOpened() and self.cap_pha.isOpened() and self.cap_distract.isOpened() and self.cap_pha_distract.isOpened()):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
            self.cap_pha.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
            self.cap_distract.set(cv2.CAP_PROP_POS_FRAMES,
                                  self.frame_idx % self.frame_count_distract)
            self.cap_pha_distract.set(cv2.CAP_PROP_POS_FRAMES,
                                      self.frame_idx % self.frame_count_distract)

            self.sl.setValue(self.frame_idx)
            # print('----', self.sl.value())
            ret, self.frame = self.cap.read()
            ret0, self.frame_pha = self.cap_pha.read()
            ret2, self.frame2 = self.cap_distract.read()
            ret3, self.frame_pha2 = self.cap_pha_distract.read()
            if ret and ret2 and ret0 and ret3:
                frame1 = cv2.cvtColor(self.frame1, cv2.COLOR_BGR2RGB)
                frame2 = cv2.cvtColor(self.frame2, cv2.COLOR_BGR2RGB)

                # setup preview
                h1, w1, b1 = frame1.shape
                b1 = b1*w1
                q_image_t = QImage(frame1.data,  w1, h1, b1,
                                   QImage.Format_RGB888).scaled(self.label_target_preview.width(), self.label_target_preview.height())
                self.label_target_preview.setPixmap(
                    QPixmap.fromImage(q_image_t))

                h2, w2, b2 = frame2.shape
                b2 = b2*w2
                q_image_d = QImage(frame2.data,  w2, h2, b2,
                                   QImage.Format_RGB888).scaled(self.label_distract_preview.width(), self.label_distract_preview.height())
                self.label_distract_preview.setPixmap(
                    QPixmap.fromImage(q_image_d))

                frame, pha_merged = composite_with_pha(
                    frame1, self.frame_pha/255, frame2, self.frame_pha2, self.compositingParams)

                # write the result to mp4

                #

                height, width, bytesPerComponent = frame.shape
                bytesPerLine = bytesPerComponent * width
                q_image = QImage(frame.data,  width, height, bytesPerLine,
                                 QImage.Format_RGB888).scaled(self.label.width(), self.label.height())
                self.label.setPixmap(QPixmap.fromImage(q_image))

                if self.frame_idx == self.frame_count_main-1:
                    if self.isPlaying:
                        self.change_playing_status()
                if self.controller == Controller.TIMER and self.frame_idx < self.frame_count_main:
                    self.frame_idx += 1
            else:
                print("### Some Caps might have been closed.")
                self.cap.release()
                self.cap_distract.release()
                self.cap_pha.release()
                self.cap_pha_distract.release()
                self.timer_camera.stop()   # 停止计时器

    def change_playing_status(self):
        if self.cap is None or self.cap_pha is None or self.cap_distract is None:
            QMessageBox.about(self, "Operate Failed",
                              "Please open video first!")
            return
        self.isPlaying = not self.isPlaying  # 取反
        if self.isPlaying == True:
            self.btn_preview.setText("Pause")
            self.btn_preview.setStyleSheet("QPushButton{background:green;}")
            self.controller = Controller.TIMER
            self.timer_camera.start(20)
            self.timer_camera.timeout.connect(self.openFrame)

        else:
            self.btn_preview.setText("Play")
            self.btn_preview.setStyleSheet("QPushButton{background:red;}")
            self.timer_camera.stop()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    v_root = '/Users/jiangxin/Project/Dataset/VideoMatte240K/train'
    target_vnames = ['0000.mp4',
                     '0003.mp4',
                     '0006.mp4',
                     '0007.mp4',
                     '0008.mp4',
                     '0010.mp4',
                     '0013.mp4',
                     '0022.mp4',
                     '0023.mp4',
                     '0024.mp4',
                     '0025.mp4',
                     '0026.mp4',
                     '0027.mp4',
                     '0028.mp4',
                     '0032.mp4',
                     '0033.mp4',
                     '0034.mp4',
                     '0037.mp4',
                     '0038.mp4',
                     '0039.mp4',
                     '0040.mp4',
                     '0042.mp4',
                     '0046.mp4',
                     '0047.mp4',
                     '0050.mp4',
                     '0051.mp4',
                     '0062.mp4',
                     '0063.mp4',
                     '0064.mp4',
                     '0067.mp4',
                     '0068.mp4',
                     '0069.mp4',
                     '0072.mp4',
                     '0073.mp4',
                     '0075.mp4',
                     '0076.mp4',
                     '0079.mp4',
                     '0081.mp4',
                     '0082.mp4',
                     '0084.mp4',
                     '0085.mp4',
                     '0090.mp4',
                     '0092.mp4',
                     '0096.mp4',
                     '0097.mp4',
                     '0098.mp4',
                     '0099.mp4',
                     '0101.mp4',
                     '0102.mp4',
                     '0103.mp4',
                     '0104.mp4',
                     '0109.mp4',
                     '0110.mp4',
                     '0120.mp4',
                     '0129.mp4',
                     '0132.mp4',
                     '0133.mp4',
                     '0134.mp4',
                     '0135.mp4',
                     '0136.mp4',
                     '0137.mp4',
                     '0138.mp4',
                     '0139.mp4',
                     '0142.mp4',
                     '0144.mp4',
                     '0145.mp4',
                     '0146.mp4',
                     '0147.mp4',
                     '0150.mp4',
                     '0151.mp4',
                     '0153.mp4',
                     '0154.mp4',
                     '0155.mp4',
                     '0156.mp4',
                     '0157.mp4',
                     '0158.mp4',
                     '0159.mp4',
                     '0160.mp4',
                     '0161.mp4',
                     '0162.mp4',
                     '0163.mp4',
                     '0169.mp4',
                     '0170.mp4',
                     '0172.mp4',
                     '0173.mp4',
                     '0175.mp4',
                     '0178.mp4',
                     '0180.mp4',
                     '0181.mp4',
                     '0182.mp4',
                     '0183.mp4',
                     '0184.mp4',
                     '0185.mp4',
                     '0186.mp4',
                     '0187.mp4',
                     '0188.mp4',
                     '0189.mp4',
                     '0191.mp4',
                     '0192.mp4',
                     '0195.mp4',
                     '0196.mp4',
                     '0198.mp4',
                     '0200.mp4', ]

    my = Video(v_root, sorted(target_vnames))
    my.show()
    sys.exit(app.exec_())
