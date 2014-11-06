# -*- coding: utf-8 -*-

# Setup script
# 1: install module
# 2: add bin/*.py to location in $PATH
# 3: add system files

import glob
import shutil
import subprocess
from setuptools import setup, find_packages

l, e = subprocess.Popen(
    ['/usr/sbin/service', 'raspalarm', 'stop']
).communicate()

if e:
    print e

setup(
    name='RaspAlarm',
    version='0.7',
    description='Package to monitor your home using Raspberry Pi',
    author=u'Sindri Guðmundsson',
    author_email='sindrigudmundsson@gmail.com',
    packages=find_packages(),
    install_requires=[
        'numpy==1.6.2',
        'PIL==1.1.7',
        'picamera==1.8',
        # 'matplotlib==1.1.1rc2',
    ],
    scripts=glob.glob('bin/*.py')
)

files_to_move = [
    ('system/raspalarm_cron', '/etc/cron.d/raspalarm'),
    ('system/raspalarm_service', '/etc/init.d/raspalarm')
]

for src, dst in files_to_move:
    shutil.copyfile(src, dst)

l, e = subprocess.Popen(
    ['/usr/sbin/service', 'raspalarm', 'start']
).communicate()

if e:
    print e
