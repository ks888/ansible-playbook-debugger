#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.abspath('lib'))
from setuptools import setup, find_packages

from ansible.debugger import __version__

setup(
    name='ansible-playbook-debugger',
    version=__version__,
    description='Debugger for ansible playbook',
    author='Kishin Yagami',
    author_email='k.yagami.suou@gmail.com',
    url='',
    license='GPLv3',
    install_requires=['ansible'],
    package_dir={'ansible.debugger': 'lib/ansible/debugger'},
    packages=find_packages('lib'),
    scripts=[
        'bin/ansible-playbook-debugger',
    ],
)
