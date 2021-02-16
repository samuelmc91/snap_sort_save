#!/usr/bin/python3
import os
import cv2
import sys
import multiprocessing

def crop_image(img, root_dir):
     sys.path.insert(0, root_dir)
     from predict_position import predict_image
     # base_x and base_y are the x and y of the first position crop
     # if the camera is moved recrop position one and set the base_x and base_y to the new x and y value
     # do not change the width or height
     fname = img.split('/')[8].split('.')[0]
     base_x = 415
     base_y = 456
     w = 143
     h = 141

     # Do not change the x and y offsets in the lists
     x = [0, 95, 252, 252, 99, -160, -114, 12,
          179, 333, 429, 429, 337, 186, 18, -112]

     y = [0, -131, -84, 78, 133, 2, -160, -274,
          -299, -231, -90, 80, 227, 295, 276, 165]

     count = 1
     img = cv2.imread(img)

     for x, y in zip(x, y):
          filename = root_dir + 'Temp/' + fname + '_' + str(count) + '.jpg'
          new_x = base_x + x
          new_y = base_y + y
          crop_img = img[new_y:new_y + h, new_x:new_x + w]
          cv2.imwrite(filename, crop_img)
          predict_image(filename, root_dir)
          count += 1
