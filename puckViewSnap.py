#!/usr/bin/python3
import time
import epics
import getpass
import os
import random
from datetime import date
import multiprocessing
import sys
import math

global today
# Check to make sure that the folder for runtime exists
if os.path.exists('/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/'):
    ROOT_DIR = '/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/'
else:
    raise RuntimeError('ROOT DIRECTORY NOT FOUND')

sys.path.insert(0, '/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/')
from crop_images import crop_image

acq = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:Acquire')
img_mode = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:ImageMode')
data_type = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:DataType')
save_file = epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:WriteFile')

position_goal = epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get()

class Watcher:
    def __init__(self, value):
        self.variable = value

    def set_value(self, new_value):
        if self.variable != new_value:
            self.pre_change()
            self.variable = new_value
            self.post_change()

    def pre_change(self):
        position_goal = int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())
        puck_check = False
        fill_check = False
        fill_level = epics.PV('XF:17IDB-ES:AMX{CS8}Ln2Level-I').get()
        user_name = getpass.getuser()
        # Input file name to CSS
        epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileName').put(user_name)

        plates = dict([(1, 180),
                  (2, 135),
                  (3, 90),
                  (4, 45),
                  (5, 0),
                  (6, 315),
                  (7, 270),
                  (8, 225)])

        degrees_high_check = position_goal + 135
        degrees_low_check = position_goal - 225

        plate = next(plate for plate, degree in plates.items() if degree == degrees_high_check or degree == degrees_low_check)
       
        ##### Comment/Uncomment below to set directory by user and not date #####
        
        if epics.PV('XF:17IDB-ES:AMX{Wago:1}Puck' + str(plate) + 'C-Sts').get() != 1:
            print('There is no puck on position: {}. No image taken'.format(plate))
        else:
            puck_check = True
        
        today = date.today().strftime('%b_%d_%Y')
        todays_dir = ROOT_DIR + 'puckSnap_' + today
        
        if os.path.exists(ROOT_DIR + 'puckSnap_' + today):
            epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(todays_dir)
        else:
            epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileNumber').put(1)
            # Joining the image path to the temporary directory for a new directory to store images
            os.system("mkdir -p " + todays_dir)
            os.system("chmod 777 " + todays_dir)
            print('Directory Created for today at: {}'.format(todays_dir))
            # Input file path to CSS
            epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(todays_dir)

        ##### Comment/Uncomment below to set directory by user and not date #####

            # epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileNumber').put(1)
            
            # # Get the username for the directory and file name
            # user_name = getpass.getuser()
            # tmp_dir = user_name + '_puckSnap_' +  str(random.randint(11111, 99999))

            # # Joining the image path to the temporary directory for a new directory to store images
            # image_path = os.path.join(ROOT_DIR, tmp_dir)
            # os.system("mkdir -p " + image_path)
            # os.system("chmod 777 " + image_path)

            # # Input file path to CSS
            # epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(image_path)
            # # Input file name to CSS
            # epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileName').put(user_name)
        
        ##### Comment/Uncomment above to set directory by user and not date #####

        if fill_level >= 85:
            fill_check = True
        else:
            print('Fill Violation, Fill Level Is: ' + str('%.2f' % fill_level))
            print('Please Fill Dewar to Continue')

        if puck_check and fill_check:   
            while math.isclose(int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.RBV').get()), int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get()), abs_tol = 2) == False:
                    print('Dewar is at: {} \nRotating to: {}'.format(int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.RBV').get()), int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())))
                    time.sleep(2)
            for i in range(1, 4):    
                # current_position = int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.RBV').get())
                # position_goal = int(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())
                # if not math.isclose(current_position,position_goal, abs_tol = 2):
                #     print('Restarted for New Rotation')
                #     break
                print('Taking image: ' + str(i) + ' of 3')

                user_name = getpass.getuser()
                inner_dir = user_name + '_puckSnap_' + str(random.randint(11111, 99999))
                inner_dir = os.path.join(todays_dir, inner_dir)
                os.system("mkdir -p " + inner_dir)
                os.system("chmod 777 " + inner_dir)
                print('Images are in: {}'.format(inner_dir))
                epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(inner_dir)

                epics.PV('XF:17IDB-ES:AMX{Cam:14}Proc1:EnableFilter').put(1)

                # Change the settings to take the picture and capture the image
                acq.put(0)
                img_mode.put(0)
                data_type.put(0)
                time.sleep(2)
                acq.put(1)
                time.sleep(2)
                save_file.put(1)

                # Put the camera back to the original settings
                time.sleep(2)
                img_mode.put(2)
                data_type.put(1)
                acq.put(1)

                img = epics.caget('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileName', as_string=True) + '_' + \
                str(epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileNumber').get() - 1).zfill(3) + '.jpg'

                try:
                    p1 = multiprocessing.Process(target=crop_image(img, inner_dir))
                    p1.start()
                except Exception as e:
                    print('Prediction Failed: {}'.format(e))
                # A fifteen second wait to allow conditions to change
                time.sleep(15)
        epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(todays_dir)
        self.post_change()

    def post_change(self):
        # Ensure the camera is returned to its normal status
        time.sleep(2)
        img_mode.put(2)
        data_type.put(1)
        acq.put(1)
        epics.PV('XF:17IDB-ES:AMX{Cam:14}Proc1:EnableFilter').put(0)
        check_for_change(epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())


def check_for_change(goal):
    while True:
        time.sleep(10)
        Watcher(goal).set_value(
            epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())
        print('Waiting for rotation')


check_for_change(position_goal)
