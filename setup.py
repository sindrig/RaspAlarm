# -*- coding: utf-8 -*-

# Setup script
# 1: install module
# 2: add bin/*.py to location in $PATH
# 3: add system files - TODO

import glob
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

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
