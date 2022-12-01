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

from utils import composite


class Controller(Enum):
    TIMER = 1
    SLIDER = 2


class Video(QWidget):

    def __init__(self, root, target_vnames, distracting_vnames=None):
        super(Video, self).__init__()
        self.root = root

        self.init_compositingParams()

        self.frame = None  # 存图片
        self.frame2 = None
        self.frame_pha = None
        self.frame_count_main = 0
        self.frame_count_distract = 0
        self.cap = None
        self.cap_pha = None
        self.cap_distract = None
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

        # select distracting video videos
        self.label_distract = QLabel(self)
        self.label_distract.setText("Distracting:")
        self.label_distract.setFixedSize(70, 20)  # width height
        self.label_distract.move(1085, 210)

        self.distracting_videos = QComboBox(self)
        self.distracting_videos.addItems(distracting_vnames)
        self.distracting_videos.move(1*pos_unit-10+1085, 210)
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
        self.btn_preview.setText("Play")
        self.btn_preview.move(5*pos_unit-40+ps_group_x_pos, 740)
        self.btn_preview.setStyleSheet(
            "QPushButton{background:red;}")  # 没检测红色，检测绿色
        self.btn_preview.clicked.connect(self.change_playing_status)
        # 关闭视频按钮
        self.btn_stop = QPushButton(self)
        self.btn_stop.setText("Stop")
        self.btn_stop.move(6*pos_unit-40+ps_group_x_pos, 740)
        self.btn_stop.clicked.connect(self.slotStop)

        # Save parameters
        self.btn_save = QPushButton(self)
        self.btn_save.setText("SaveParams")
        self.btn_save.move(7*pos_unit-40+ps_group_x_pos, 740)
        self.btn_save.clicked.connect(self.save_params)
        ## *******\end Play and Stop buttong ***********#####

        self.frame_idx = 0

        # progress bar for playing video
        self.sl = QSlider(Qt.Horizontal, self)
        self.sl.setMinimum(0)
        self.sl.setMaximum(0)
        self.sl.setValue(self.frame_idx)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(10)
        self.sl.setGeometry(10, 740, 760, 40)
        # self.sl.move(240, 740)
        self.sl.sliderPressed.connect(self.sl_clicked)
        # self.sl.sliderMoved.connect(self.sl_moved)

        # *****************  edit zoom_rate x_offset y_offset for distracting video ************************** #
        # zoom_rate controller
        group_pos_v = 40

        self.label_zoom = QLabel(self)
        self.label_zoom.setText("zoom_rate(%):")
        self.label_zoom.setFixedSize(85, 20)  # width height
        self.label_zoom.move(1090, 420+group_pos_v)

        self.e_zoom_rate = QLineEdit(self)
        self.e_zoom_rate.setValidator(QIntValidator())
        self.e_zoom_rate.setMaxLength(3)
        self.e_zoom_rate.setAlignment(Qt.AlignRight)
        self.e_zoom_rate.setFixedSize(60, 20)
        self.e_zoom_rate.move(1200, 420+group_pos_v)
        self.e_zoom_rate.setText(str(self.compositingParams['zoom_rate']))
        self.e_zoom_rate.returnPressed.connect(self.e_zoom_rate_textChanged)

        self.sl_zoom = QSlider(Qt.Horizontal, self)
        self.sl_zoom.setMinimum(0)
        self.sl_zoom.setMaximum(100)
        self.sl_zoom.setValue(self.compositingParams['zoom_rate'])
        self.sl_zoom.setTickPosition(QSlider.TicksBelow)
        self.sl_zoom.setTickInterval(10)
        self.sl_zoom.setGeometry(1100, 450+group_pos_v, 200, 30)
        self.sl_zoom.sliderMoved.connect(self.sl_zoom_moved)

        # y_offset
        self.label_y_offset = QLabel(self)
        self.label_y_offset.setText("y_offset:")
        self.label_y_offset.setFixedSize(85, 20)  # width height
        self.label_y_offset.move(1090, 480+group_pos_v)

        self.e_y_offset = QLineEdit(self)
        self.e_y_offset.setValidator(QIntValidator())
        self.e_y_offset.setMaxLength(5)
        self.e_y_offset.setAlignment(Qt.AlignRight)
        self.e_y_offset.setFixedSize(60, 20)
        self.e_y_offset.move(1200, 480+group_pos_v)
        self.e_y_offset.setText(str(self.compositingParams['y_offset']))
        self.e_y_offset.returnPressed.connect(self.e_y_offset_textChanged)
        self.e_y_offset

        self.sl_y_offset = QSlider(Qt.Horizontal, self)
        self.sl_y_offset.setMinimum(0)
        self.sl_y_offset.setMaximum(100)
        self.sl_y_offset.setValue(self.compositingParams['y_offset'])
        self.sl_y_offset.setTickPosition(QSlider.TicksBelow)
        self.sl_y_offset.setTickInterval(10)
        self.sl_y_offset.setGeometry(1100, 510+group_pos_v, 200, 30)
        self.sl_y_offset.sliderMoved.connect(self.sl_y_offset_moved)

        # x_offset
        self.label_x_offset = QLabel(self)
        self.label_x_offset.setText("x_offset:")
        self.label_x_offset.setFixedSize(85, 20)  # width height
        self.label_x_offset.move(1090, 550+group_pos_v)

        self.e_x_offset = QLineEdit(self)
        self.e_x_offset.setValidator(QIntValidator())
        self.e_x_offset.setMaxLength(5)
        self.e_x_offset.setAlignment(Qt.AlignRight)
        self.e_x_offset.setFixedSize(60, 20)
        self.e_x_offset.move(1200, 550+group_pos_v)
        self.e_x_offset.setText(str(self.compositingParams['x_offset']))
        self.e_x_offset.returnPressed.connect(self.e_x_offset_textChanged)

        self.sl_x_offset = QSlider(Qt.Vertical, self)
        self.sl_x_offset.setMinimum(0)
        self.sl_x_offset.setMaximum(100)
        self.sl_x_offset.setValue(self.compositingParams['x_offset'])
        self.sl_x_offset.setTickPosition(QSlider.TicksBelow)
        self.sl_x_offset.setTickInterval(10)
        self.sl_x_offset.setGeometry(1200, 580+group_pos_v, 30, 180)
        self.sl_x_offset.sliderMoved.connect(self.sl_x_offset_moved)

        # self.max_x_offset = None
        # self.max_y_offset = None

        # ******************************************* #

        self.controller = Controller.TIMER

    def init_compositingParams(self):
        self.compositingParams = {
            'zoom_rate': 100,
            'x_offset': 0,
            'y_offset': 0,
        }

    def slotStart(self):
        """ Slot function to start the progamme
            """
        self.init_compositingParams()
        # videoName, _ = QFileDialog.getOpenFileName(
        #     self, "Open", self.root, "*.mp4;;All Files(*)")
        target_vname0 = self.target_videos.currentText()
        target_vname = os.path.join(self.root, 'fgr', target_vname0)
        target_pha_vname = os.path.join(self.root, 'pha', target_vname0)
        distract_vname = self.distracting_videos.currentText()
        distract_vname = os.path.join(self.root, 'fgr', distract_vname)

        if self.cap != None:
            self.cap.release()
        if self.cap_pha != None:
            self.cap_pha.release()
        if self.cap_distract != None:
            self.cap_distract.release()

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
            self.sl_x_offset.setMaximum(self.height)
            self.sl_y_offset.setMaximum(self.width)
            self.sl_x_offset.setMinimum(-self.height)
            self.sl_y_offset.setMinimum(-self.width)

            self.cap_distract = cv2.VideoCapture(distract_vname)
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

        if (self.cap.isOpened()):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
            self.cap_distract.set(cv2.CAP_PROP_POS_FRAMES,
                                  self.frame_idx % self.frame_count_distract)
            self.sl.setValue(self.frame_idx)
            # print('----', self.sl.value())
            ret, self.frame = self.cap.read()
            ret0, self.frame_pha = self.cap_pha.read()
            ret2, self.frame2 = self.cap_distract.read()
            if ret and ret2 and ret0:
                frame1 = cv2.cvtColor(
                    (self.frame_pha/255*self.frame).astype(np.uint8), cv2.COLOR_BGR2RGB)
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

                frame = composite(frame1, frame2, self.compositingParams)

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
                print("### Cap is closed.")
                self.cap.release()
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

    def sl_clicked(self):
        if self.isPlaying:
            self.change_playing_status()
        self.controller = Controller.SLIDER
        self.frame_idx = self.sl.value()
        cv2.waitKey(10)
        self.openFrame()

    def sl_moved(self):
        if self.isPlaying:
            self.change_playing_status()
        self.controller = Controller.SLIDER
        self.frame_idx = self.sl.value()
        self.openFrame()

    def sl_zoom_moved(self):
        val = self.sl_zoom.value()
        self.e_zoom_rate.setText(str(val))
        self.openFrame()

    def e_zoom_rate_textChanged(self):
        text = self.e_zoom_rate.text()
        if text is not None and text != '' and text != ' ':
            val = int(text)
            print('zoom_rate: ', val)
            val = 100 if val > 300 else val
            val = 1 if val < 1 else val
            self.e_zoom_rate.setText(str(val))
            self.compositingParams['zoom_rate'] = val
            self.sl_zoom.setValue(val)
            self.openFrame()
            # print(int(text))

    def sl_x_offset_moved(self):
        val = self.sl_x_offset.value()
        self.e_x_offset.setText(str(val))
        self.openFrame()

    def e_x_offset_textChanged(self):
        text = self.e_x_offset.text()
        if text is not None and text != '' and text != ' ' and text != '-':
            val = int(text)
            val = self.sl_x_offset.maximum() if val > self.sl_x_offset.maximum() else val
            val = -self.sl_x_offset.maximum() if val < -self.sl_x_offset.maximum() else val
            self.e_x_offset.setText(str(val))
            self.compositingParams['x_offset'] = val
            self.sl_x_offset.setValue(-val)
            self.openFrame()

    def sl_y_offset_moved(self):
        val = self.sl_y_offset.value()
        self.e_y_offset.setText(str(val))
        self.openFrame()

    def e_y_offset_textChanged(self):
        text = self.e_y_offset.text()
        if text is not None and text != '' and text != ' ' and text != '-':
            val = int(text)
            val = self.sl_y_offset.maximum() if val > self.sl_y_offset.maximum() else val
            val = -self.sl_y_offset.maximum() if val < -self.sl_y_offset.maximum() else val
            self.e_y_offset.setText(str(val))
            self.compositingParams['y_offset'] = val
            self.sl_y_offset.setValue(val)
            self.openFrame()


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
    distracting_vnames = ['0001.mp4',
                          '0002.mp4',
                          '0004.mp4',
                          '0005.mp4',
                          '0009.mp4',
                          '0011.mp4',
                          '0012.mp4',
                          '0014.mp4',
                          '0015.mp4',
                          '0016.mp4',
                          '0017.mp4',
                          '0018.mp4',
                          '0019.mp4',
                          '0020.mp4',
                          '0021.mp4',
                          '0029.mp4',
                          '0030.mp4',
                          '0031.mp4',
                          '0035.mp4',
                          '0036.mp4',
                          '0041.mp4',
                          '0043.mp4',
                          '0044.mp4',
                          '0045.mp4',
                          '0048.mp4',
                          '0049.mp4',
                          '0052.mp4',
                          '0053.mp4',
                          '0054.mp4',
                          '0055.mp4',
                          '0056.mp4',
                          '0057.mp4',
                          '0058.mp4',
                          '0059.mp4',
                          '0060.mp4',
                          '0061.mp4',
                          '0065.mp4',
                          '0066.mp4',
                          '0070.mp4',
                          '0071.mp4',
                          '0074.mp4',
                          '0077.mp4',
                          '0078.mp4',
                          '0080.mp4',
                          '0083.mp4',
                          '0086.mp4',
                          '0087.mp4',
                          '0088.mp4',
                          '0089.mp4',
                          '0091.mp4',
                          '0093.mp4',
                          '0094.mp4',
                          '0095.mp4',
                          '0100.mp4',
                          '0105.mp4',
                          '0106.mp4',
                          '0107.mp4',
                          '0108.mp4',
                          '0111.mp4',
                          '0112.mp4',
                          '0113.mp4',
                          '0114.mp4',
                          '0115.mp4',
                          '0116.mp4',
                          '0117.mp4',
                          '0118.mp4',
                          '0119.mp4',
                          '0121.mp4',
                          '0122.mp4',
                          '0123.mp4',
                          '0124.mp4',
                          '0125.mp4',
                          '0126.mp4',
                          '0127.mp4',
                          '0128.mp4',
                          '0130.mp4',
                          '0131.mp4',
                          '0140.mp4',
                          '0141.mp4',
                          '0143.mp4',
                          '0148.mp4',
                          '0149.mp4',
                          '0152.mp4',
                          '0164.mp4',
                          '0165.mp4',
                          '0166.mp4',
                          '0167.mp4',
                          '0168.mp4',
                          '0171.mp4',
                          '0174.mp4',
                          '0176.mp4',
                          '0177.mp4',
                          '0179.mp4',
                          '0190.mp4',
                          '0193.mp4',
                          '0194.mp4',
                          '0197.mp4',
                          '0199.mp4', ]
    my = Video(v_root, sorted(target_vnames), sorted(distracting_vnames))
    my.show()
    sys.exit(app.exec_())
