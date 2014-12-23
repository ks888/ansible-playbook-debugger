#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.abspath('lib'))
from setuptools import setup, find_packages

from ansibledebugger import __version__

setup(
    name='ansible-playbook-debugger',
    version=__version__,
    description='Debugger for Ansible Playbook',
    author='Kishin Yagami',
    author_email='k.yagami.suou@gmail.com',
    url='https://github.com/ks888/ansible-playbook-debugger',
    license='GPLv3',
    install_requires=['ansible'],
    packages=find_packages('lib'),
    package_dir={'ansibledebugger': 'lib/ansibledebugger'},
    scripts=[
        'bin/ansible-playbook-debugger',
    ],
    zip_safe=False,
)
