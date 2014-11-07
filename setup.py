# -*- coding: utf-8 -*-

# Setup script
# 1: install module
# 2: add bin/*.py to location in $PATH
# 3: add system files

import glob
import os
import sys
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
        'matplotlib==1.1.1rc2',
        'requests',
        'pushbullet.py',
        'python-magic'
    ],
    data_files=[
        ('/etc/init.d', ['system/raspalarm']),
        ('/etc/cron.d', ['system/raspalarm.cron']),
        ('/etc/raspalarm', ['system/raspalarm.conf']),
        (
            os.path.join(sys.prefix, 'raspalarm', 'web', 'www'),
            glob.glob('raspalarm/web/www/*')
        )
    ],
    scripts=glob.glob('bin/*.py')
)

l, e = subprocess.Popen(
    ['/usr/sbin/service', 'raspalarm', 'start']
).communicate()

if e:
    print e
