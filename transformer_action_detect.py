# -*- coding: utf-8 -*-
"""transformer-action-detect

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ExXkJEkBOuR-u88_X1i-aKdubahIGZiq

#**Library**
"""

"""# getAngle

"""
import os
import math

import matplotlib.pyplot as plt
import numpy as np
import torch

import easydict
from sklearn.model_selection import train_test_split


def getAngle(start, mid, end):
        """
        Calculate the angle between start and end
        :param start: start point [x, y]
        :param end: mid point [x, y]
        :param end: end point [x, y]
        :return: the clockwise angle from start to end
        """
        v1 = np.array([0,0])
        v2 = np.array([0,0])

        v1[0] = (start[0]-mid[0])
        v1[1] = (start[1]-mid[1])

        v2[0] = (end[0]-mid[0])
        v2[1] = (end[1]-mid[1])
       #  angle = np.arccos((v1[0]*v2[0]+v1[1]*v2[1])/(math.sqrt(v1[0]*v1[0] + v1[1]*v1[1])*math.sqrt(v2[0]*v2[0] + v2[1]*v2[1]))*math.pi/180)

        #a = (v1[0]*v2[0]+v1[1]*v2[1])
        k = v1[0]*v1[0] + v1[1]*v1[1]
        j = v2[0]*v2[0] + v2[1]*v2[1]
        if k==0 or j==0 :
          angle = 0
        else:
          b = math.sqrt(k)*math.sqrt(j)
          c = np.inner(v1,v2)/b
          angle = 0
          if c <= 1 and c >=-1 :
            angle = np.arccos(c)
        #  print(c)
        #  print('각도:')
       #   print(angle*180/math.pi)
        
        return angle*180/math.pi

getAngle([1,0],[0,0],[1,1])

getAngle([0,0], [0,0],[0,0])

getAngle([1,1.717], [0,0],[1,0])

# pose= np.load('label_yerim/label_9/cat-sitdown-098036.npy')
# #print(type(data))
# #print(data.shape)
# #print(data)

# df = pd.read_csv('/content/label_yerim/label_8.csv')

# lab = df['action']
# filename = df['filename']

# label = lab.values.tolist()
# file_list = filename.values.tolist()

# print(df)

"""ㅇ#**dataset.py**"""


class trainDataset(torch.utils.data.Dataset):

    def __init__(self, data_path='./data', kps = None):
        train_dir_list = ['label_7', 'label_8', 'label_9']
        label_dir_list = ['label_7.csv', 'label_8.csv', 'label_9.csv']
        self.data_path = data_path

        self.exclude_labels = [ "4", "5", "6", "8", "9"]
        self.label_num = 12 - len(self.exclude_labels)
        self.count_limit = 1467

        self.angle_sets = [[2, 26, 28], [2, 8, 26], [8, 10, 14], [8, 12, 16], [22, 18, 26], [24, 20, 26]]
        self.angle_num = len(self.angle_sets)
        self.kps = kps

        self.label_map = {}
        self.label_key = {}

        # 제외할 라벨 및 개수 제한
        self._dataFlattening(label_dir_list)

    def __len__(self):
        return len(self.train_videos)

    def __getitem__(self, idx):
        filename, label = self.train_videos[idx]
        video_data = np.load(os.path.join(self.data_path, filename))
        #     angle_lists = []
        #     for angle_set in self.angle_sets:
        angle_list = self._getAngle(video_data, self.kps)
        #         angle_lists.append(angle_list)
        #     item = (np.array(angle_lists), label)
        item = (angle_list, label)
        # print(item)
        return item

    def _dataFlattening(self, label_dir_list):
        import csv

        print("creating dataset")

        self.vid_dict = {}  # {"3": ['021314-cat-grooming.mp4', ... ], ... }
        self.act_dict = {}  # {"3": "그루밍 함", ...}
        for csv_file in label_dir_list:
            filepath = os.path.join(self.data_path, csv_file)
            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                for info in reader:
                    act_id = info['action_id']

                    # * action이랑 인덱스 매칭 (필수는 아니지만 시각적인 도움)
                    if not self.act_dict.get(str(act_id), None):
                        self.act_dict[str(act_id)] = info['action']

                    # * self.exclude_labels 안에 있는 데이터들은 제외해주기!!
                    if act_id in self.exclude_labels:
                        if not isinstance(self.vid_dict.get(str(act_id), None), list):
                            self.vid_dict[str(act_id)] = []
                        continue
                    vid_list = self.vid_dict.get(act_id, [])

                    # 갯수 제한 있을 경우
                    if self.count_limit:
                        if len(vid_list) >= self.count_limit:
                            continue

                    filename = info['filename']
                    src = csv_file.split(".")[0]
                    filename = os.path.join(src, filename + ".npy")  # label_7/203030_cat-grooming-1234.mp4.npy

                    vid_list.append(filename)
                    self.vid_dict[act_id] = vid_list

        # 데이터를 줄였을때, 라벨링 값의 범위를 개수에 맞춰 줄여주기 위한 코드 (안줄이면 label 범위 (1,12), 3개 줄이면 (1, 9))
        # 주의! 이 개수에 맞춰 모델구조 다시 구성해줘야함
        # self.label_map = {'3': (0, '그루밍함'), '12': (1, '걷거나 뛰는 동작'), '7': (2, '꼬리를 흔든다'), '11': (3, '팔을 뻗어 휘적거림')}
        self.train_videos = []
        label = 0
        for i, k in enumerate(self.vid_dict):
            # ("13213-cat-grooming.mp4.npy", label:int) 형태로 리스트에 추가!
            for vid in self.vid_dict[k]:
                if not self.label_map.get(str(k), None):
                    self.label_map[str(k)] = (label, self.act_dict[str(k)], str(k))
                    self.label_key[str(label)] = str(k)
                    label += 1
                self.train_videos.append((vid, self.label_map[str(k)][0]))

        # print(self.label_map)
        # print(self.train_videos)
        self._showActdict()

    def _showActdict(self):
        for i in range(1, 13):
            print(f"act_id: {str(i)} | {self.act_dict[str(i)]} | {len(self.vid_dict[str(i)])}")

    def _getAngle(self, video_data, kps):
        angle_list = []
        angle_sett = kps
        s, m, f = angle_sett[0], angle_sett[1], angle_sett[2]

        '''
keypoints 1  2   3   4    5   6         7       8       9         10        11      12      13        14      15
         코 머리 입 입끝 목 앞우관절 앞좌관절 앞우발끝 앞좌발끝 뒤우관절 뒤좌관절 뒤우발끝 뒤좌발끝 꼬리시작 꼬리끝
          0    2   4  6    8    10      12         14     16        18      20        22        24     26    28
         다리각도 정도랑/ 꼬리/ 머리 목 다리/
        '''

        for i in range(0, 30):
            start_point = list()
            mid_point = list()
            end_point = list()
            if video_data[i][s] != 0:
                start_point.append(video_data[i][s])
                start_point.append(video_data[i][s + 1])
            else:
                if len(angle_list) == 0:
                    angle_list.append(0)
                else:
                    angle_list.append(angle_list[-1])

                continue;
            ####
            if video_data[i][m] != 0:
                mid_point.append(video_data[i][m])
                mid_point.append(video_data[i][m + 1])
            else:
                if len(angle_list) == 0:
                    angle_list.append(0)
                else:
                    angle_list.append(angle_list[-1])

                continue;
            #####
            if video_data[i][f] != 0:
                end_point.append(video_data[i][f])
                end_point.append(video_data[i][f + 1])
            else:
                if len(angle_list) == 0:
                    angle_list.append(0)
                else:
                    angle_list.append(angle_list[-1])

                continue;
            ######
            angle = getAngle(start_point, mid_point, end_point)
            angle_list.append(angle)

        return angle_list


"""#**<main**>"""




if __name__ == "__main__":
    # 1 2 3 7 10 11 12
    args = easydict.EasyDict({
        "batch_size": 8,
        "epoch": 200,
        "loss_interval": 500,
        "split_training": False,
        "data_path": 'data/label_yerim/',
        "model_name": 'transformer-action-detect.pth',
        "model_path": './output/'})

    kpss = [[2,8,14],[2,8,26],[2,26,28],[18,26,20],[22,26,24],[14,26,22],[14,8,22],[10,8,12],[14,8,16]]

    for kps in kpss:
        dataset = trainDataset(args.data_path, kps)
        train_dataset, valid_dataset = train_test_split(dataset, test_size=0.2, shuffle=True, random_state=34)
        folder_path = f"output/images/{str(kps)}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        label1 = []
        label2 = []
        label3 = []
        label4 = []
        label5 = []
        label6 = []
        label7 = []
        for i in range(7500):
            a = train_dataset[i]
            if a[1] == 0:
                label1.append(a[0])
            if a[1] == 1:
                label2.append(a[0])
            if a[1] == 2:
                label3.append(a[0])
            if a[1] == 3:
                label4.append(a[0])
            if a[1] == 4:
                label5.append(a[0])
            if a[1] == 5:
                label6.append(a[0])
            if a[1] == 6:
                label7.append(a[0])
        colors = ["red", "blue", "green", "m", "y", "k", "orange",]
        labels = ["getdown", "sit", "grooming", "tail", "lay", "arm-swing", "runwalk"]
        for i in range(800):

            lab1 = label1[i]
            lab2 = label2[i]
            lab3 = label3[i]
            lab4 = label4[i]
            lab5 = label5[i]
            lab6 = label6[i]
            lab7 = label7[i]

            labs = [lab1, lab2, lab3, lab4, lab5, lab6, lab7]

            plt.xlim([0, 30])
            plt.ylim([-5, 180])
            fig, axs = plt.subplots(4,2)
            fig.tight_layout(pad=2.0)

            for id in range(7):
                r = id % 4
                c = id // 4
                axs[r, c].plot(labs[id], colors[id])
                axs[r, c].set_ylabel(labels[id])
                axs[r, c].set_ylim([-5, 180])
            plt.savefig(f"output/images/{str(kps)}/{i}.jpg")
            plt.close()

            #
            #
            # plt.show()



