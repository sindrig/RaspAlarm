#!/usr/bin/env python

import os
import glob
import time

def read():
    # load the kernel modules needed to handle the sensor
    os.system('sudo modprobe w1-gpio')
    os.system('sudo modprobe w1-therm')

    # find the path of a sensor directory that starts with 28
    devicelist = glob.glob('/sys/bus/w1/devices/28*')
    # append the device file name to get the absolute path of the sensor
    devicefile = devicelist[0] + '/w1_slave'

    # open the file representing the sensor.
    line = None
    with open(devicefile, 'r') as f:
        for line in f:
            pass
    if line:
        tmp = line.strip().split()
        temp_str_w_t = tmp[-1]
        temp_str = temp_str_w_t.split('=')[-1]
        temp = float(temp_str) / 1000
        return temp
    return 0.0

if __name__ == '__main__':
    print read()
