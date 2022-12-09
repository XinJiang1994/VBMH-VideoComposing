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


def merge_pha(pha_target, pha_distract):
    '''
    hint:
    1. Firstly, define a new variable pha_merged, and let pha_merged = pha_distract.copy(), think about it, why we use .copy() here.
    2. Replace the pha_merged vaules with pha_target values where pha_target>0,
       for example: pha_merged[pha_target>0] = pha_target[pha_target>0]
    3. return pha_merged
    '''
    pha_merged = pha_distract.copy()
    pha_merged[pha_target>0] = pha_target[pha_target>0]
    return pha_merged



def composite_video(frame_target, frame_distract, pha_target, pha_distract):
    '''
    1. 去除frame_target的背景（借助pha_target），存储在 frame_target_new 中；
    2. 去除frame_distract的背景（借助pha_distract）存储在 frame_distract_new 中；
    3. 定义一个与新变量： frame_composited=frame_distract_new
    4. 将 frame_composited 中对应 pha_target>0 的部分的值替换成 frame_target_new 的值，
       例如：frame_composited[ha_target>0] = frame_target_new[ha_target>0]
    5. 返回 frame_composited
    '''
    frame_target_new = frame_target.copy()
    frame_target_new[pha_target==0] = 0
    frame_distract_new = frame_distract.copy()
    frame_distract_new[pha_distract==0] = 0
    frame_composited = frame_distract_new
    frame_composited[pha_target>0] = frame_target_new[pha_target>0]
    return frame_composited


def composite_with_pha(frame_target, pha_target, frame_distract, pha_distract, params):
    '''
    frame_target: a frame from target video, it's a numpy array with shape of (H,W,C), 
                  where H is image height, W is width, C is channel.
                  The value of frame_target is 0-255.

    pha_target: The alpha matte corresponding to the frame_target. The shape is (H,W,C) which is the same with frame_target.
                It's a float array and the value is 0.0-1.0

    frame_distract: distracting frame

    pha_distract: distracting alpha matte

    params: the compositing params, 
            for example: {"zoom_rate": 40, "x_offset": 650, "y_offset": 300, "distract": "0002.mp4"}


    ToDo: 
    1. generate the merged alpha matte using the given params, see the above function: merge_pha(pha_target, pha_distract)
    2. the composited frame using the given params, see the above function composite_video(frame_target, frame_distract, pha_target, pha_distract).

    '''
    merged_pha = merge_pha(pha_target, pha_distract)
    composited_frame = composite_video(
        frame_target, frame_distract, pha_target, pha_distract)
    return composited_frame, merged_pha
