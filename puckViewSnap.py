#!/usr/bin/python3
import time
import epics
import getpass
import os
import random
from datetime import date
import multiprocessing
import sys

global today
# Check to make sure that the folder for runtime exists
if os.path.exists('/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/'):
    ROOT_DIR = '/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/'
else:
    raise RuntimeError('ROOT DIRECTORY NOT FOUND')

sys.path.insert(0, '/GPFS/CENTRAL/XF17ID2/sclark1/puck_visualization_system/snap_sort_save/')
from crop_images import crop_image

start_date = date.today().strftime('%b_%d_%Y')
if os.path.exists(ROOT_DIR + 'puckSnap_' + start_date):
    today = date.today()
else:
    today = ''

acq = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:Acquire')
img_mode = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:ImageMode')
data_type = epics.PV('XF:17IDB-ES:AMX{Cam:14}cam1:DataType')
save_file = epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:WriteFile')

position_goal = epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get()


class plate_check:
    def __init__(self, plate, degree):
        self.plate = plate
        self.degree = degree


class Watcher:
    def __init__(self, value):
        self.variable = value

    def set_value(self, new_value):
        if self.variable != new_value:
            self.pre_change()
            self.variable = new_value
            self.post_change()

    def pre_change(self):
        puck_check = False
        fill_check = False
        fill_level = epics.PV('XF:17IDB-ES:AMX{CS8}Ln2Level-I').get()
        user_name = getpass.getuser()
        # Input file name to CSS
        epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileName').put(user_name)

        plates = (plate_check(1, 180),
                  plate_check(2, 135),
                  plate_check(3, 90),
                  plate_check(4, 45),
                  plate_check(5, 0),
                  plate_check(6, 315),
                  plate_check(7, 270),
                  plate_check(8, 225))
        holder = 0
        ##### Comment/Uncomment below to set directory by user and not date #####
        for plate in plates:
             if (epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get() + 135) == plate.degree or (epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get() - 225) == plate.degree:
                    holder = plate.plate
        if epics.PV('XF:17IDB-ES:AMX{Wago:1}Puck' + str(holder) + 'C-Sts').get() != 1:
            print('There is no puck on position: {}. No image taken'.format(holder))
        else:
            puck_check = True
            global today
            if date.today() != today:
                today = date.today()
                date_dir = today.strftime('%b_%d_%Y')
                tmp_dir = 'puckSnap_' + date_dir
                epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FileNumber').put(1)
                # Joining the image path to the temporary directory for a new directory to store images
                image_path = os.path.join(ROOT_DIR, tmp_dir)
                os.system("mkdir -p " + image_path)
                os.system("chmod 777 " + image_path)
                print('Directory Created for today at: {}'.format(image_path))
                # Input file path to CSS
                epics.PV('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath').put(image_path)


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
            # A one and a half minute buffer to allow the dewar to rotate
            time.sleep(20)
            file_path = epics.caget('XF:17IDB-ES:AMX{Cam:14}JPEG1:FilePath', as_string=True)
            print('Images are in: {}'.format(file_path))
            epics.PV('XF:17IDB-ES:AMX{Cam:14}Proc1:EnableFilter').put(1)
            for i in range(1, 4):
                print('Taking image: ' + str(i) + ' of 3')
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

                img = epics.caget('XF:17IDB-ES:AMX{Cam:14}JPEG1:FullFileName_RBV', as_string=True)
                try:
                    p1 = multiprocessing.Process(target=crop_image(img, ROOT_DIR))
                    p1.start()
                except Exception:
                    print('Prediction Failed')
                # A one minute wait to allow conditions to change
                time.sleep(15)
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
        time.sleep(5)
        Watcher(goal).set_value(
            epics.PV('XF:17IDB-ES:AMX{Dew:1-Ax:R}Mtr.VAL').get())
        print('Waiting for rotation')


check_for_change(position_goal)
