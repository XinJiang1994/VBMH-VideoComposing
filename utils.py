import numpy as np
import cv2


def composite(frame1, frame2, params):
    print(f'frame1.shape:{frame1.shape}, frame2.shape:{frame2.shape}')
    h, w = frame1.shape[:2]
    # frame2 = cv2.resize(frame2, (w, h), None)

    zoom_rate = params['zoom_rate']/100
    x_offset = params['x_offset']
    y_offset = params['y_offset']
    # print("###", params)
    bg = np.zeros_like(frame1)

    # zoom frame2
    org_h2, org_w2 = frame2.shape[:2]
    new_h, new_w = int(org_h2*zoom_rate), int(org_w2*zoom_rate)
    frame2 = cv2.resize(frame2, (new_w, new_h), None)

    # area to be replaced before move
    idx_x1_1 = 0
    idx_y1_1 = 0
    idx_x1_2 = min(h, new_h)
    idx_y1_2 = min(w, new_w)

    idx_x2_1 = 0
    idx_y2_1 = 0
    idx_x2_2 = min(h, new_h)
    idx_y2_2 = min(w, new_w)

    # area to be replace for target after move
    idx_x1_1 = x_offset if x_offset > 0 else 0
    idx_y1_1 = y_offset if y_offset > 0 else 0
    if new_h+x_offset <= 0 or new_w+y_offset <= 0:
        return frame1
    idx_x1_2 = new_h+x_offset if new_h+x_offset < h else h
    idx_y1_2 = new_w+y_offset if new_w+y_offset < w else w

    # area to be seleceted for distracting video after move
    idx_x2_1 = 0 if x_offset >= 0 else -x_offset
    idx_y2_1 = 0 if y_offset >= 0 else -y_offset
    if x_offset < 0:
        idx_x2_2 = min(
            new_h, h-x_offset)
    elif new_h < h-x_offset:
        idx_x2_2 = new_h
    else:
        idx_x2_2 = h-x_offset

    idx_y2_2 = min(
        new_w, w-y_offset) if y_offset < 0 else min(w-y_offset, new_w)
    print(
        f"frame1 idx:({idx_x1_1},{idx_y1_1}),({idx_x1_2},{idx_y1_2})<--->frame2 idx:({idx_x2_1},{idx_y2_1}),({idx_x2_2},{idx_y2_2})")
    bg[idx_x1_1:idx_x1_2, idx_y1_1:idx_y1_2] = frame2[idx_x2_1:idx_x2_2, idx_y2_1:idx_y2_2]
    frame1[frame1 == 0] = bg[frame1 == 0]
    return frame1
